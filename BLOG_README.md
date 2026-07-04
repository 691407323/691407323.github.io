# 简单博客模板使用说明

一个极简静态博客生成器，将 Markdown 文章渲染为纯 HTML 静态站点。内置暗色模式、代码复制、阅读时间、标签、归档、RSS、搜索、评论、公式、图表等特性（详见 [IMPLEMENTATION.md](IMPLEMENTATION.md)）。

## 文件结构

```
Blog/
├── build.py                  # 构建脚本（唯一生成逻辑）
├── requirements.txt          # Python 依赖
├── BLOG_README.md            # 本说明（面向写作者）
├── IMPLEMENTATION.md         # 实现说明（面向维护者）
├── README.md                 # 仓库简介（指向上述文档）
├── PLAN.md                   # 功能拓展计划与状态
├── .gitignore
├── .github/workflows/
│   └── deploy.yml            # GitHub Pages 自动部署
├── content/
│   ├── posts/
│   │   └── *.md              # Markdown 博客文章（YAML front matter）
│   └── aboutme.md            # 关于页面源文件
├── templates/
│   ├── base.html             # 基础骨架（head/header/导航/footer + KaTeX/Mermaid CDN）
│   ├── index.html            # 首页模板（文章列表）
│   ├── post.html             # 文章详情（目录/标签/系列导航/评论）
│   ├── about.html            # 关于页
│   ├── tags.html             # 标签总览（标签云）
│   ├── tag.html              # 单标签文章列表
│   ├── archive.html          # 按年份归档
│   ├── search.html           # 站内搜索页
│   └── feed.xml              # RSS/Atom Feed 模板
└── static/
    ├── css/style.css         # 全局样式（CSS 变量 + 暗色模式）
    ├── js/
    │   ├── theme.js          # 暗色模式切换 + Mermaid 主题同步
    │   ├── code-copy.js      # 代码块一键复制
    │   └── search.js         # FlexSearch 站内搜索逻辑
    └── images/               # 图片资源（写作者手动放置）
```

## 如何添加文章

在 [content/posts/](content/posts/) 新建 `.md` 文件，开头添加 YAML front matter。

### Front Matter 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `title` | 否 | 文章标题，默认取文件名 |
| `date` | 否 | 发布日期（YYYY-MM-DD），用于排序降序 |
| `slug` | 否 | URL 友好标识，默认取文件名（不可重复，重复构建报错） |
| `tags` | 否 | 文章标签，数组 `[a, b]` 或逗号字符串 `"a, b"` |
| `description` | 否 | 文章摘要（用于 RSS summary、SEO description） |
| `draft` | 否 | 布尔，`true` 时跳过构建（不计入标签/归档/RSS） |
| `linenums` | 否 | 布尔，`true` 时该篇代码块显示行号 |
| `cover` | 否 | 封面图路径（**不带前导斜杠**，如 `static/images/x.png`），生成 og:image |
| `updated` | 否 | 最后修改日期（YYYY-MM-DD），文章页显示"更新于"，RSS 优先使用 |
| `series` | 否 | 系列名，配合 `series_order` 生成系列导航 |
| `series_order` | 否 | 该篇在系列中的序号（按此升序排列） |

### 最小示例

```markdown
---
title: 使用 Docker 部署 Python 应用
date: 2026-05-28
slug: docker-python-deploy
tags: [Docker, Python, 部署]
description: 容器化部署 Python Web 应用。
---

本文演示如何使用 Docker 容器化部署一个 Python Web 应用。

## Dockerfile 示例

\`\`\`dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "app.py"]
\`\`\`
```

### 富功能示例（标签/封面/系列/公式/图表/脚注）

```markdown
---
title: TSTL 插件架构
date: 2025-03-16
slug: tstl-plugin-architecture
tags: [TSTL, TypeScript, Lua, 架构]
description: TSTL 插件架构原理与扩展点。
cover: static/images/tstl-arch.png
series: TSTL 系列
series_order: 2
---

架构示意 ` ```mermaid ` 图：

\`\`\`mermaid
graph LR
A[源码] --> B[编译器] --> C[Lua 输出]
\`\`\`

概率公式 `$$P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}$$`（块级用 `$$...$$`，行内用 `\(...\)`）。

带脚注的文字[^1]。

[^1]: 脚注内容会渲染到页面底部。
```

### 支持的 Markdown 语法

| 语法 | 写法 | 说明 |
|------|------|------|
| 标题 | `## 二级标题`、`### 三级标题` | 最多六级 |
| 粗体 / 斜体 | `**粗体**` / `*斜体*` | 也支持 `__` / `_` |
| 行内代码 | `` `print("hello")` `` | 灰色背景高亮 |
| 代码块 | ` ```python ` … ` ``` ` | 自动语法高亮，`<code class="language-python">` |
| 代码行号 | front matter `linenums: true` | 仅该篇代码块显示行号 |
| 无序/有序列表 | `- 项目` / `1. 项目` | 支持嵌套 |
| 引用 | `> 引用文字` | 支持 `>>` 嵌套 |
| 链接 | `[文字](https://url)` | |
| 图片 | `![替代文字](/static/images/x.png)` | **必须用绝对路径 `/static/...`** |
| 分隔线 | `---` 或 `***` | |
| 脚注 | `[^1]` + `[^1]: 内容` | 自动渲染到页面底部 |
| 数学公式 | `$$...$$` 块级 / `\(...\)` 行内 | KaTeX 渲染，不用 `$...$` 避免与文本冲突 |
| Mermaid 图表 | ` ```mermaid ` … ` ``` ` | 流程图/架构图，CDN 渲染 |
| HTML | `<details>`、`<kbd>` 等 | 原生 HTML 可直接嵌入 |

> 注：删除线（`~~删除~~`）、任务列表（`- [ ]`）、Markdown 表格（`| 列A |...|`）当前**未启用**对应扩展，不会渲染——需表格可改用 HTML `<table>`，需删除线/复选框可改用原生 HTML。

## 添加图片

1. 把图片放进 `static/images/`（**手写绝对路径，不自动替换**）
2. 正文用绝对路径引用：`![alt](/static/images/xxx.png)`
3. 封面图用 front matter `cover: static/images/xxx.png`（不带前导斜杠）

> 自适应已内置：`.post-body img { max-width:100% }`。**已支持自动 WebP 压缩**：构建时 `static/images/` 中的 PNG/JPG 会生成同名 `.webp`（限宽 1600px）和 `_thumb.webp` 缩略图；文中建议引用 `.webp` 以省体积（原始文件也保留，仍可引用 PNG）。

参考示范文章 [content/posts/image-usage-demo.md](content/posts/image-usage-demo.md)。

## 现有文章

| 文件 | 说明 |
|------|------|
| [markdown-guide.md](content/posts/markdown-guide.md) | Markdown 语法全面演示 |
| [docker-python-deploy.md](content/posts/docker-python-deploy.md) | 多语言代码高亮 + 表格 |
| [skynet-cmake-usage.md](content/posts/skynet-cmake-usage.md) | Skynet 跨平台构建 |
| [tstl-plugin-architecture.md](content/posts/tstl-plugin-architecture.md) | TSTL 插件架构 |
| [tstl-to-lua-about.md](content/posts/tstl-to-lua-about.md) | TSTL 改动 |
| [image-usage-demo.md](content/posts/image-usage-demo.md) | 图片插入示例 |

## 构建站点

```bash
# 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 构建
python build.py
```

构建完成后，`_site/` 目录即为完整静态站点：

```
_site/
├── index.html              # 首页（按日期倒序）
├── posts/<slug>.html       # 各文章详情页
├── about.html              # 关于页
├── tags.html               # 标签总览
├── tags/<encoded>.html     # 各标签文章页
├── archive.html            # 按年份归档
├── search.html             # 搜索页
├── search-index.json       # FlexSearch 索引
├── feed.xml                # RSS/Atom 订阅源
└── static/                 # css/js/images 副本
```

## 本地预览

```bash
cd _site && python3 -m http.server 8000
# 浏览器访问 http://localhost:8000
```

## 部署到 GitHub Pages

推送到 `main` 分支即自动触发 [deploy.yml](.github/workflows/deploy.yml)，将 `_site/` 部署到 `gh-pages` 分支。

需在仓库 Settings → Pages 中将 Source 设为 "Deploy from a branch"，分支选 `gh-pages`、目录选 `/ (root)`。

## 特性速览

- 暗色模式（跟随系统 + 手动切换，记忆偏好）
- 代码块一键复制（移动端长按可见）
- 阅读时间估算（中英文分计）
- 标签系统（标签云 + 单标签页，中文 URL 编码）
- 按年份归档
- RSS/Atom 订阅源
- 站内搜索（FlexSearch，仅搜索页加载）
- Giscus 评论（pathname 映射）
- KaTeX 数学公式
- Mermaid 图表
- 文章系列导航（上一篇/下一篇 + 系列列表）
- Open Graph / SEO Meta

详见 [IMPLEMENTATION.md](IMPLEMENTATION.md) 与 [PLAN.md](PLAN.md)。
