#!/usr/bin/env python3
"""
Simple static blog builder: Markdown → Jinja2 → HTML
"""
from pathlib import Path
import shutil
import re
import sys
import json
from datetime import datetime, timezone
from urllib.parse import quote
from collections import defaultdict

import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader

# ============================================================
# 站点全局配置（所有模块统一引用）
# ============================================================
SITE_CONFIG = {
    'domain': '691407323.github.io',
    'title': '胤源 Blog',
    'start_year': 2021,
    'author': '胤源',
    'description': '极简静态博客，Markdown 写作，Python 构建',
    # M-12: Giscus 评论（留空则不显示评论区）
    'giscus_repo': '691407323/691407323.github.io',
    'giscus_repo_id': 'R_kgDOSqX-lw',
    'giscus_category': 'Announcements',
    'giscus_category_id': 'DIC_kwDOSqX-l84DAdPg',
}

# ============================================================
# Markdown 公共扩展配置
# ============================================================
COMMON_MD_EXT = ['fenced_code', 'toc', 'codehilite', 'footnotes']
# codehilite 配置不在公共字典中预置：linenums 按 front matter 逐篇控制，
# 在创建 Markdown 实例时单独传入，避免与 per-post 覆盖产生冗余。
COMMON_MD_CFG = {
    'toc': {'title': '', 'toc_depth': 3},
}
# M-08 / M-09 扩展按需追加到上面两个列表
OPTIONAL_MD_EXT = []
OPTIONAL_MD_CFG = {}

# M-08: KaTeX 数学公式（可选，需安装 pymdownx.arithmatex）
try:
    import pymdownx.arithmatex
    OPTIONAL_MD_EXT.append('pymdownx.arithmatex')
    OPTIONAL_MD_CFG['pymdownx.arithmatex'] = {'generic': True}
except ImportError:
    pass  # 未安装则跳过，不影响构建

# ============================================================
# M-09: Mermaid 图表自定义 Markdown 扩展
# preprocessor 优先级 50，高于 fenced_code_block（约 25），
# 因此先于 fenced_code 执行，把 ```mermaid 块替换成 <div class="mermaid">，
# 使 base.html 的 Mermaid CDN 能识别并渲染为图表。
# ============================================================
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


class MermaidPreprocessor(Preprocessor):
    def run(self, lines):
        in_m = False
        result = []
        for line in lines:
            if line.strip().startswith('```mermaid'):
                in_m = True
                result.append('<div class="mermaid">')
            elif in_m and line.strip() == '```':
                in_m = False
                result.append('</div>')
            elif in_m:
                result.append(line)
            else:
                result.append(line)
        return result


class MermaidExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MermaidPreprocessor(md), 'mermaid', 50)


OPTIONAL_MD_EXT.append(MermaidExtension())


# ============================================================
# M-13: 图片优化（WebP + 缩略图）
# 软依赖 Pillow：未安装时跳过图片处理，不影响构建。
# 关键决策（与 PLAN.md 一致）：不自动改写 Markdown 图片路径，
# 写作者须手写 /static/images/xxx(.webp) 绝对路径。
# ============================================================
try:
    from PIL import Image
except ImportError:
    Image = None  # M-13 未安装 Pillow 时跳过图片处理


def process_images(images_dir, max_width=1600, thumb_width=480, quality=82):
    """扫描 images_dir，对 PNG/JPG(JPEG) 生成同名 .webp + _thumb.webp 缩略图。

    已存在的 .webp 不重转（按修改时间判断：源图更新才重生成）。
    返回 (生成数, 跳过数) 供调用方统计。
    """
    if Image is None:
        print('M-13: Pillow 未安装，跳过图片优化')
        return 0, 0
    src_dir = Path(images_dir)
    if not src_dir.exists():
        return 0, 0
    generated = skipped = 0
    for img in sorted(src_dir.iterdir()):
        if img.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
            continue
        webp = img.with_suffix('.webp')
        thumb = img.with_name(f'{img.stem}_thumb.webp')
        # 源图未更新且产物已存在 → 跳过
        if webp.exists() and thumb.exists() \
           and webp.stat().st_mtime >= img.stat().st_mtime:
            skipped += 1
            continue
        with Image.open(img) as im:
            im = im.convert('RGB')  # 抹掉 alpha 等 WebP 不友好成分
            # 主图：限制最大宽度
            if im.width > max_width:
                ratio = max_width / im.width
                im = im.resize((max_width, int(im.height * ratio)))
            im.save(webp, 'WEBP', quality=quality, method=6)
            # 缩略图：固定宽度等比缩放
            t_ratio = thumb_width / im.width
            t = im.resize((thumb_width, int(im.height * t_ratio)))
            t.save(thumb, 'WEBP', quality=quality, method=6)
        generated += 1
        print(f'  M-13: {img.name} -> {webp.name} + {thumb.name}')
    return generated, skipped


def load_posts(dirpath):
    p = Path(dirpath)
    if not p.exists():
        return []
    raw_posts = []
    for md_file in sorted(p.glob('*.md')):
        post = frontmatter.load(md_file)
        meta = dict(post.metadata)
        if meta.get('draft'):
            continue  # draft 跳过构建
        raw_posts.append({'post': post, 'meta': meta, 'src': md_file})

    posts = []
    for item in raw_posts:
        post = item['post']
        meta = item['meta']
        md_file = item['src']
        meta.setdefault('title', md_file.stem)
        meta['date'] = str(meta.get('date', ''))
        meta.setdefault('slug', meta.get('slug', md_file.stem))
        # linenums 按 front matter 控制
        linenums = meta.get('linenums', False)
        md = markdown.Markdown(
            extensions=COMMON_MD_EXT + OPTIONAL_MD_EXT,
            extension_configs={**COMMON_MD_CFG, **OPTIONAL_MD_CFG,
                              'codehilite': {'linenums': linenums, 'css_class': 'highlight'}},
        )
        html = md.convert(post.content)
        toc_html = md.toc
        if '<li>' not in toc_html:
            toc_html = ''
        langs = re.findall(r'^```(\S*)', post.content, re.MULTILINE)
        def _add_lang(m):
            lang = langs.pop(0) if langs else ''
            cls = f' class="language-{lang}"' if lang else ''
            return m.group(1) + cls + '>'
        html = re.sub(r'(<div class="codehilite"><pre><span></span><code>)', _add_lang, html)
        read_time = _estimate_read_time(html)
        posts.append({'meta': meta, 'content': html, 'toc': toc_html, 'src': md_file, 'read_time': read_time})

    # slug 碰撞检查
    slugs = {}
    for p_item in posts:
        s = p_item['meta'].get('slug', p_item['src'].stem)
        if s in slugs:
            print(f'Error: Slug collision! "{s}" from {p_item["src"].name} conflicts with {slugs[s].name}')
            sys.exit(1)
        slugs[s] = p_item['src']
    posts.sort(key=lambda x: x['meta'].get('date', ''), reverse=True)
    return posts


def _estimate_read_time(html_content):
    """估算阅读时间（中文400字/分钟，英文200词/分钟）"""
    text = re.sub(r'<[^>]+>|\s+', '', html_content)
    cn = len(re.findall(r'[一-鿿㐀-䶿！？　-〿]', text))
    en = len(re.findall(r'[a-zA-Z]+', text))
    minutes = cn / 400 + en / 200
    return '< 1 分钟' if minutes < 1 else f'{int(minutes)} 分钟'


def build():
    root = Path(__file__).resolve().parent
    env = Environment(loader=FileSystemLoader(root / 'templates'))
    out = root / '_site'
    try:
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)

        # M-13: 先优化源 static/images/（生成 WebP + 缩略图），再让 copytree 一并带走产物
        images_src = root / 'static' / 'images'
        if images_src.exists():
            gen, skip = process_images(images_src)
            if Image is not None:
                print(f'M-13 图片优化完成：{gen} 张生成，{skip} 张跳过')

        # copy static
        static_dir = root / 'static'
        if static_dir.exists():
            shutil.copytree(static_dir, out / 'static')

        posts = load_posts(root / 'content/posts')

        start_year = SITE_CONFIG['start_year']
        current_year = datetime.now().year
        site_title = SITE_CONFIG['title']

        # 构建标签索引（M-04）
        all_tags = {}
        all_tag_url_map = {}
        for p_item in posts:
            tags = p_item['meta'].get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]
            p_item['meta']['tags_list'] = tags
            for tag in tags:
                all_tags.setdefault(tag, []).append({
                    'title': p_item['meta'].get('title', ''),
                    'slug': p_item['meta']['slug'],
                    'date': p_item['meta'].get('date', ''),
                })
                if tag not in all_tag_url_map:
                    all_tag_url_map[tag] = quote(tag, safe='')

        # 构建系列索引（M-10）
        series_map = {}
        for p_item in posts:
            series = p_item['meta'].get('series')
            if series:
                series_map.setdefault(series, []).append({
                    'title': p_item['meta'].get('title', ''),
                    'slug': p_item['meta']['slug'],
                    'date': p_item['meta'].get('date', ''),
                    'series_order': p_item['meta'].get('series_order', 0),
                })
        for sp_list in series_map.values():
            sp_list.sort(key=lambda x: x['series_order'])

        # 构建归档（M-05）
        archive = defaultdict(list)
        for p_item in posts:
            date_str = p_item['meta'].get('date', '')
            if not date_str:
                continue
            year = date_str[:4]
            archive[year].append({
                'title': p_item['meta'].get('title', ''),
                'slug': p_item['meta']['slug'],
                'date': date_str,
            })
        archive = dict(sorted(archive.items(), reverse=True))

        # render posts（M-01~M-10 + M-14 SEO 数据注入）
        for p_item in posts:
            tpl = env.get_template('post.html')
            slug = p_item['meta']['slug']
            title = p_item['meta'].get('title', '') + ' · ' + site_title
            current_series = p_item['meta'].get('series')
            series_nav = None
            if current_series and current_series in series_map:
                sp_list = series_map[current_series]
                idx = next((i for i, sp in enumerate(sp_list) if sp['slug'] == slug), -1)
                if idx >= 0:
                    series_nav = {
                        'prev': sp_list[idx - 1] if idx > 0 else None,
                        'next': sp_list[idx + 1] if idx < len(sp_list) - 1 else None,
                        'list': sp_list,
                        'name': current_series,
                    }
            # M-14: og:image 由 front matter cover 字段生成绝对 URL（留空则不输出）
            cover = p_item['meta'].get('cover', '')
            og_image = f"https://{SITE_CONFIG['domain']}/{cover.lstrip('/')}" if cover else ''
            html = tpl.render(
                title=title,
                post=p_item['meta'],
                content=p_item['content'],
                toc=p_item['toc'],
                site_title=site_title,
                start_year=start_year,
                current_year=current_year,
                read_time=p_item['read_time'],
                tags_list=p_item['meta'].get('tags_list', []),
                all_tag_url_map=all_tag_url_map,
                series_nav=series_nav,
                description=p_item['meta'].get('description', ''),
                site_description=SITE_CONFIG['description'],
                site_author=SITE_CONFIG['author'],
                canonical_url=f"https://{SITE_CONFIG['domain']}/posts/{p_item['meta']['slug']}.html",
                og_type='article',
                og_title=p_item['meta'].get('title', ''),
                og_description=p_item['meta'].get('description', ''),
                og_image=og_image,
                keywords=', '.join(p_item['meta'].get('tags_list', [])),
                giscus_repo=SITE_CONFIG.get('giscus_repo', ''),
                giscus_repo_id=SITE_CONFIG.get('giscus_repo_id', ''),
                giscus_category=SITE_CONFIG.get('giscus_category', 'Announcements'),
                giscus_category_id=SITE_CONFIG.get('giscus_category_id', ''),
            )
            dest = out / 'posts' / f"{slug}.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding='utf-8')

        # render about page
        about_file = root / 'content' / 'aboutme.md'
        if about_file.exists():
            about_post = frontmatter.load(about_file)
            about_meta = dict(about_post.metadata)
            about_md = markdown.Markdown(extensions=COMMON_MD_EXT + OPTIONAL_MD_EXT,
                                         extension_configs={**COMMON_MD_CFG, **OPTIONAL_MD_CFG,
                                                           'codehilite': {'linenums': False, 'css_class': 'highlight'}})
            about_html = about_md.convert(about_post.content)
            tpl = env.get_template('about.html')
            about_title = about_meta.get('title', '关于我') + ' · ' + site_title
            about_page = tpl.render(
                title=about_title,
                content=about_html,
                site_title=site_title,
                start_year=start_year,
                current_year=current_year,
                description=about_meta.get('description', ''),
                site_description=SITE_CONFIG['description'],
                site_author=SITE_CONFIG['author'],
                canonical_url=f"https://{SITE_CONFIG['domain']}/about.html",
                og_type='website',
                og_title=about_meta.get('title', '关于我'),
                og_description=about_meta.get('description', SITE_CONFIG['description']),
            )
            (out / 'about.html').write_text(about_page, encoding='utf-8')

        # render index
        tpl = env.get_template('index.html')
        index_html = tpl.render(
            title=site_title,
            posts=[{'title': p['meta']['title'], 'date': p['meta'].get('date', ''), 'slug': p['meta'].get('slug')} for p in posts],
            site_title=site_title,
            start_year=start_year,
            current_year=current_year,
            description=SITE_CONFIG['description'],
            site_description=SITE_CONFIG['description'],
            site_author=SITE_CONFIG['author'],
            canonical_url=f"https://{SITE_CONFIG['domain']}/",
            og_type='website',
            og_title=SITE_CONFIG['title'],
            og_description=SITE_CONFIG['description'],
        )
        (out / 'index.html').write_text(index_html, encoding='utf-8')

        # M-04: 渲染标签总览页
        tag_index_for_render = {}
        for tag, tposts in all_tags.items():
            enc = all_tag_url_map[tag]
            tag_index_for_render[enc] = {'name': tag, 'posts': tposts, 'url': enc}
        tpl = env.get_template('tags.html')
        tags_html = tpl.render(
            tag_index=tag_index_for_render,
            title='标签 · ' + site_title,
            site_title=site_title, start_year=start_year, current_year=current_year,
            description=SITE_CONFIG['description'],
            site_description=SITE_CONFIG['description'],
            site_author=SITE_CONFIG['author'],
            canonical_url=f"https://{SITE_CONFIG['domain']}/tags.html",
            og_type='website',
            og_title='标签 · ' + site_title,
            og_description=SITE_CONFIG['description'],
        )
        (out / 'tags.html').write_text(tags_html, encoding='utf-8')

        # M-04: 渲染每个标签的独立页面
        for tag, tposts in all_tags.items():
            enc = all_tag_url_map[tag]
            tpl = env.get_template('tag.html')
            tag_html = tpl.render(
                tag_name=tag, tag_url=enc, tag_posts=tposts,
                title=f'{tag} · ' + site_title,  # 独立标签页需要独立 title（之前漏传导致 <title> 为空）
                description=SITE_CONFIG['description'],
                site_title=site_title, start_year=start_year, current_year=current_year,
                site_description=SITE_CONFIG['description'],
                site_author=SITE_CONFIG['author'],
                canonical_url=f"https://{SITE_CONFIG['domain']}/tags/{enc}.html",
                og_type='website',
                og_title=f'{tag} · {site_title}',
                og_description=f'标签「{tag}」下的全部文章。',
            )
            (out / 'tags' / f'{enc}.html').parent.mkdir(parents=True, exist_ok=True)
            (out / 'tags' / f'{enc}.html').write_text(tag_html, encoding='utf-8')

        # M-05: 渲染归档页
        tpl = env.get_template('archive.html')
        archive_html = tpl.render(
            archive=archive,
            title='文章归档 · ' + site_title,
            site_title=site_title, start_year=start_year, current_year=current_year,
            description=SITE_CONFIG['description'],
            site_description=SITE_CONFIG['description'],
            site_author=SITE_CONFIG['author'],
            canonical_url=f"https://{SITE_CONFIG['domain']}/archive.html",
            og_type='website',
            og_title=SITE_CONFIG['title'],
            og_description=SITE_CONFIG['description'],
        )
        (out / 'archive.html').write_text(archive_html, encoding='utf-8')

        # M-06: 生成 RSS/Atom Feed
        current_date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        tpl = env.get_template('feed.xml')
        feed_html = tpl.render(
            posts=[{
                'title': p_item['meta'].get('title', ''),
                'slug': p_item['meta']['slug'],
                'date': p_item['meta'].get('date', ''),
                'updated': p_item['meta'].get('updated', ''),
                'description': p_item['meta'].get('description', '') or p_item['meta'].get('title', ''),
                'content': p_item['content'],
            } for p_item in posts],
            site_title=site_title,
            site_domain=SITE_CONFIG['domain'],
            current_date=current_date,
            start_year=start_year,
            current_year=current_year,
        )
        (out / 'feed.xml').write_text(feed_html, encoding='utf-8')

        # M-11: 生成搜索索引
        search_index = []
        for p_item in posts:
            text = re.sub(r'<[^>]+>', '', p_item['content'])
            text = re.sub(r'\s+', ' ', text)
            search_index.append({
                'title': p_item['meta'].get('title', ''),
                'slug': p_item['meta']['slug'],
                'date': p_item['meta'].get('date', ''),
                'tags': p_item['meta'].get('tags_list', []),
                'content': text,
                'excerpt': text[:300],
            })
        (out / 'search-index.json').write_text(
            json.dumps(search_index, ensure_ascii=False),
            encoding='utf-8',
        )

        # M-11: 渲染搜索页
        tpl = env.get_template('search.html')
        search_html = tpl.render(
            title='搜索 · ' + site_title,
            site_title=site_title, start_year=start_year, current_year=current_year,
            description=SITE_CONFIG['description'],
            site_description=SITE_CONFIG['description'],
            site_author=SITE_CONFIG['author'],
            canonical_url=f"https://{SITE_CONFIG['domain']}/search.html",
            og_type='website',
            og_title='搜索 · ' + site_title,
            og_description=SITE_CONFIG['description'],
        )
        (out / 'search.html').write_text(search_html, encoding='utf-8')

        print('Built site -> _site/')
    except Exception as e:
        print(f'Build failed: {e}')
        raise


if __name__ == '__main__':
    build()
