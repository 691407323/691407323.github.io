#!/usr/bin/env python3
"""
Simple static blog builder:
- Reads markdown files from content/posts/*.md (YAML front matter supported)
- Renders posts with Jinja2 templates in templates/
- Outputs static site to _site/
"""
from pathlib import Path
import shutil
import re
import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader
from datetime import datetime


def load_posts(dirpath):
    p = Path(dirpath)
    posts = []
    if not p.exists():
        return posts
    for md_file in sorted(p.glob('*.md')):
        post = frontmatter.load(md_file)
        meta = dict(post.metadata)
        meta.setdefault('title', md_file.stem)
        meta.setdefault('date', '')
        meta.setdefault('slug', meta.get('slug', md_file.stem))
        md = markdown.Markdown(extensions=['fenced_code', 'toc', 'codehilite'], extension_configs={'toc': {'title': '', 'toc_depth': 3}})
        html = md.convert(post.content)
        toc_html = md.toc
        # Only treat TOC as present if it contains actual links
        if '<li>' not in toc_html:
            toc_html = ''
        # Post-process: add language-* class to <code> tags inside codehilite blocks
        langs = re.findall(r'^```(\S*)', post.content, re.MULTILINE)
        def _add_lang(m):
            lang = langs.pop(0) if langs else ''
            cls = f' class="language-{lang}"' if lang else ''
            return m.group(1) + cls + '>'
        html = re.sub(r'(<div class="codehilite"><pre><span></span><code)>', _add_lang, html)
        posts.append({'meta': meta, 'content': html, 'toc': toc_html, 'src': md_file})
    posts.sort(key=lambda x: x['meta'].get('date', ''), reverse=True)
    return posts


def build():
    root = Path(__file__).resolve().parent
    env = Environment(loader=FileSystemLoader(root / 'templates'))
    out = root / '_site'
    try:
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)

        # copy static
        static_dir = root / 'static'
        if static_dir.exists():
            shutil.copytree(static_dir, out / 'static')

        posts = load_posts(root / 'content/posts')

        # compute years for footer and site title
        start_year = 2015
        current_year = datetime.now().year
        site_title = '胤源 Blog'

        # render posts
        for p in posts:
            tpl = env.get_template('post.html')
            html = tpl.render(post=p['meta'], content=p['content'], toc=p['toc'], site_title=site_title, start_year=start_year, current_year=current_year)
            slug = p['meta']['slug']
            dest = out / 'posts' / f"{slug}.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding='utf-8')

        # render about page
        about_file = root / 'content' / 'aboutme.md'
        if about_file.exists():
            about_post = frontmatter.load(about_file)
            about_meta = dict(about_post.metadata)
            about_md = markdown.Markdown(extensions=['fenced_code', 'toc', 'codehilite'])
            about_html = about_md.convert(about_post.content)
            tpl = env.get_template('about.html')
            about_page = tpl.render(content=about_html, title=about_meta.get('title', '关于我'), site_title=site_title, start_year=start_year, current_year=current_year)
            (out / 'about.html').write_text(about_page, encoding='utf-8')

        # render index
        tpl = env.get_template('index.html')
        index_html = tpl.render(posts=[{'title': p['meta']['title'], 'date': p['meta'].get('date', ''), 'slug': p['meta'].get('slug')} for p in posts], site_title=site_title, start_year=start_year, current_year=current_year)
        (out / 'index.html').write_text(index_html, encoding='utf-8')

        print('Built site -> _site/')
    except Exception as e:
        print(f'Build failed: {e}')
        raise


if __name__ == '__main__':
    build()
