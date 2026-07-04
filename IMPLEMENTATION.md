# 博客系统实现说明

## 概述

基于 **Markdown → Jinja2 → HTML** 的极简静态博客系统。由单一 Python 脚本 [build.py](build.py) 一键将 Markdown 文章渲染为完整 HTML 静态站点，无需数据库、无需后端运行时。功能按 [PLAN.md](PLAN.md) 分 Stage 1-4 实施，14 个模块（M-01~M-14）全部实现，覆盖暗色模式、代码复制、阅读时间、标签、归档、RSS、搜索、评论、公式、图表、系列导航、SEO、图片优化。

## 实现架构

```
content/posts/*.md ──┐
content/aboutme.md  ──┤
templates/*.html    ──┼──► build.py ──► _site/
static/{css,js}/   ──┘                  ├── index.html        首页
                                        ├── posts/<slug>.html 文章详情
                                        ├── about.html        关于
                                        ├── tags.html + tags/<enc>.html
                                        ├── archive.html      归档
                                        ├── search.html       搜索
                                        ├── search-index.json 搜索索引
                                        ├── feed.xml          RSS/Atom
                                        └── static/           css/js/images 副本
```

## 全局配置：SITE_CONFIG

[build.py](build.py) 顶部集中定义站点元数据，所有模块统一引用，杜绝散落硬编码：

```python
SITE_CONFIG = {
    'domain': '691407323.github.io',
    'title': '胤源 Blog',
    'start_year': 2021,
    'author': '胤源',
    'description': '极简静态博客，Markdown 写作，Python 构建',
    'giscus_repo': '691407323/691407323.github.io',
    'giscus_repo_id': 'R_kgDOSqX-lw',
    'giscus_category': 'Announcements',
    'giscus_category_id': 'DIC_kwDOSqX-lw84DAdPg',
}
```

## Markdown 公共扩展配置

两处 Markdown 实例（`load_posts` 与 about 渲染）共用配置，保证 aboutme.md 也继承新扩展：

```python
COMMON_MD_EXT = ['fenced_code', 'toc', 'codehilite', 'footnotes']
COMMON_MD_CFG = {'toc': {'title': '', 'toc_depth': 3}}
# codehilite 不在公共字典预置：linenums 按 front matter 逐篇控制，
# 创建实例时单独传入（css_class 统一为 'highlight'），避免冗余覆盖。
OPTIONAL_MD_EXT = []
OPTIONAL_MD_CFG = {}
# 可选追加：pymdownx.arithmatex（generic: True，输出 arithmatex 占位供 KaTeX auto-render 识别）
#            MermaidExtension()
```

实例创建形如：

```python
md = markdown.Markdown(
    extensions=COMMON_MD_EXT + OPTIONAL_MD_EXT,
    extension_configs={**COMMON_MD_CFG, **OPTIONAL_MD_CFG,
                      'codehilite': {'linenums': linenums, 'css_class': 'highlight'}},
)
```

## build.py 流程（三步）

### Step 1: 读取文章 (`load_posts`)

- 扫描 `content/posts/*.md`，用 `python-frontmatter` 解析 YAML front matter
- `draft: true` 的文章**跳过构建**（不计入标签/归档/RSS）
- 代码行号按 front matter `linenums` 逐篇控制
- 扩展链：`fenced_code` + `toc` + `codehilite` + `footnotes` + 可选 `pymdownx.arithmatex` + 可选 `MermaidExtension`
- 正则后处理：从原始 Markdown 提取代码块语言标识，注入 `<code class="language-xxx">`（Pygments codehilite 默认不带）
- 阅读时间估算（[build.py](build.py) `_estimate_read_time`）：中文 400 字/分钟、英文 200 词/分钟
- **slug 碰撞检查**：重复 slug 直接报错退出
- 按 `date` 降序排列

### Step 2: 构建索引

| 索引 | 用途 | 来源字段 |
|------|------|----------|
| `all_tags` + `all_tag_url_map` | 标签页 + post 标签链接 | `tags`，中文用 `urllib.parse.quote` 编码 |
| `series_map` | 系列导航（prev/next + 列表） | `series` + `series_order` |
| `archive` | 按年份归档 | `date` 取前 4 位 |
| `search_index` | FlexSearch 索引 | 正文去 HTML 标签 → 压缩多余空白 → 前 300 字作 excerpt |

### Step 3: 渲染模板

各页面前 5 个变量为通用 SEO/品牌项（`site_title`、`start_year`、`current_year`、`site_description`、`site_author`），下表省略不列，仅列差异化变量：

| 模板 | 差异化注入变量 |
|------|----------------|
| [post.html](templates/post.html) | `title`、`post`、`content`、`toc`、`tags_list`、`all_tag_url_map`、`series_nav`、`read_time`、`description`、`canonical_url`、`og_type`(article)、`og_title`、`og_description`、`og_image`(由 `cover` 生成，无封面则空)、`keywords`(tags 拼接)、`giscus_repo/repo_id/category/category_id`(空则不渲染评论) |
| [index.html](templates/index.html) | `posts`(标题/日期/slug)、`title`、`description`、`canonical_url`、`og_*` |
| [about.html](templates/about.html) | `title`、`content`、`description`、`canonical_url`、`og_*` |
| [tags.html](templates/tags.html) | `tag_index`、`title`、`description`、`canonical_url`、`og_*` |
| [tag.html](templates/tag.html) | `tag_name`、`tag_url`、`tag_posts` |
| [archive.html](templates/archive.html) | `archive`、`title`、`description`、`canonical_url`、`og_*` |
| [search.html](templates/search.html) | `title`、`description`、`canonical_url`、`og_*`(FlexSearch CDN 由模板内 `{% block extra_scripts %}` 加载) |
| [feed.xml](templates/feed.xml) | `posts`(含 `updated`)、`site_title`、`site_domain`、`current_date`、`start_year`、`current_year` |

## 模块清单（对照 PLAN.md）

| 模块 | 功能 | 实现要点 |
|------|------|----------|
| M-01 | 暗色模式 | CSS 变量体系 + base.html class 重构 + [theme.js](static/js/theme.js)（localStorage 记忆，跟随系统）；Mermaid 主题仅在手动切换时同步（初始加载固定 `default`，不跟随系统暗色） |
| M-02 | 代码块复制 | [code-copy.js](static/js/code-copy.js)，Clipboard API + execCommand fallback（兼容 file://） |
| M-03 | 阅读时间 | `_estimate_read_time`，CJK/英文分计 |
| M-04 | 标签系统 | 标签云 + 单标签页 + post 内联标签（数据见 Step 2 `all_tags` 索引） |
| M-05 | 归档页 | 按年份分组，无日期文章不入归档（数据见 Step 2 `archive` 索引） |
| M-06 | RSS/Atom Feed | [feed.xml](templates/feed.xml)，`SITE_CONFIG['domain']` 统一域名，`updated` 优先于 `date` |
| M-07 | front matter 拓展 | tags / draft / description / cover / updated / linenums / series / series_order |
| M-08 | KaTeX 公式 | pymdownx.arithmatex（generic mode）+ base.html CDN auto-render，分隔符仅 `$$ $$` / `\(\)` / `\[\]`（不用 `$`，避免与文本冲突） |
| M-09 | Mermaid 图表 | 自定义 `MermaidExtension`：preprocessor 优先级 50（详见下"关键技术决策"）+ base.html CDN |
| M-10 | 系列导航 | `series_map` 先构建完毕再进 render loop，标注 prev/next（数据见 Step 2 `series_map` 索引） |
| M-11 | 站内搜索 | FlexSearch 0.7.31，CDN **仅搜索页**（extra_scripts 块），防抖 + 标题命中优先（数据见 Step 2 `search_index`） |
| M-12 | Giscus 评论 | `data-mapping="pathname"`（pathname 唯一，避免 title 冲突）；`{% if giscus_repo %}` 守卫——未配置则不渲染评论区 |
| M-13 | 图片 WebP 压缩 | `process_images()` 已实现并接入 `build()`（见上"图片处理"），PNG/JPG→WebP+缩略图，增量跳过；依赖 Pillow，未安装自动跳过 |
| M-14 | Open Graph / SEO | `og:image` 条件输出（仅 `cover` 存在时），各页 `og:type` 区分 |

## 关键技术决策

### Mermaid preprocessor 优先级
Python-Markdown 的 preprocessor "**优先级值越大越先执行**"（Registry 按优先级从高到低排序）。`MermaidExtension` 注册 priority=50，fenced_code_block 约为 25，因此 Mermaid **先于** fenced_code 执行，抢先把 ` ```mermaid ` 替换成 `<div class="mermaid">`，使 base.html 的 Mermaid CDN 能识别渲染。

> ⚠️ PLAN.md 第 580 行注释"优先级必须低于 fenced_code（50 < 175）"有两处错误：方向说反了（值越大才越先），且 fenced_code 的 preprocessor 实际优先级约是 25（PLAN 写的 175 把 fenced_code_block **extension** 内部某个值当成 preprocessor 优先级）。代码 `priority=50` 的实际行为正确——先于 fenced_code 抢到 mermaid fence。

### codehilite 配置逐篇覆盖
`codehilite` 不放在公共 `COMMON_MD_CFG`，而在创建 Markdown 实例时单独传入 `linenums`（取自 front matter），实现 per-post 行号控制，避免与公共配置的冗余覆盖。`css_class` 统一为 `highlight`。

### 图片处理（M-13）
软依赖 Pillow：[build.py](build.py) 的 `process_images()` 在 `build()` 复制 static 目录**之前**对 `static/images/` 执行：PNG/JPG → WebP（主图限宽 1600px）+ 缩略图（宽 480px），源图未更新则跳过（增量优化）。构建日志输出 `M-13 图片优化完成：N 张生成，M 张跳过`。Pillow 未安装时打印跳过提示、不报错。

**Markdown 图片路径不自动改写**：写作者在文中仍写 `/static/images/xxx.png`（或 `.webp`，建议引用已生成的 `.webp` 以获得体积收益）；front matter `cover` 字段经 `cover.lstrip('/')` 处理（带或不带前导斜杠均可，不带更规范），拼成绝对 URL 生成 `og:image`。

### CDN 按需加载（原始字节 / gzip 后约 1/3）
- KaTeX：CSS ~23KB + JS ~277KB + auto-render ~3.5KB = **约 304KB**：全局（base.html head）
- Mermaid min.js：**约 3.3MB**：全局（base.html head），建议后续改按需加载
- FlexSearch bundle：**约 16.6KB**：**仅搜索页**（search.html 的 extra_scripts 块）

## 样式说明（CSS 变量体系）

[style.css](static/css/style.css) 顶部定义 `:root` 与 `[data-theme="dark"]` 两套 CSS 变量（`--bg-primary`、`--text-primary`、`--border-color`、`--tag-bg` 等）。M-01 已把 base.html 中所有颜色相关内联 style 改为 class（`.nav-link`、`.footer-text` 等），使暗色模式能自动切换。代码块深色背景始终保留，不随主题切换。

## 构建产物

见 [BLOG_README.md](BLOG_README.md) "构建站点" 部分。

## 依赖

| 包 | 用途 |
|---|---|
| `Jinja2` | HTML 模板引擎 |
| `Markdown` | Markdown → HTML |
| `python-frontmatter` | 解析 YAML front matter |
| `Pygments` | 代码语法高亮 |
| `pymdownx.arithmatex`（可选） | KaTeX 公式渲染，未安装自动跳过 |
| `Pillow`（可选） | M-13 图片 WebP/缩略图，已接入 `build()`；未安装自动跳过 |

CI/CD 见 [BLOG_README.md](BLOG_README.md) "部署到 GitHub Pages"。
