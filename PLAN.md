# 博客系统拓展计划

> 基于现有极简静态博客架构（`Markdown → Jinja2 → HTML`），按优先级分阶段实施。

---

## 目录

- [一、现有架构与现状](#一现有架构与现状)
- [二、前置准备](#二前置准备)
- [三、Stage 1：核心体验](#三stage-1核心体验)
- [四、Stage 2：博客导航](#四stage-2博客导航)
- [五、Stage 3：内容表达](#五stage-3内容表达)
- [六、Stage 4：深度扩展](#六stage-4深度扩展)
- [七、实施路线](#七实施路线)
- [八、注意事项](#八注意事项)

---

## 一、现有架构与现状

### 数据流

```
content/posts/*.md ──► build.py ──► _site/
                             ├─ index.html        首页
                             ├─ posts/<slug>.html  文章详情
                             ├─ about.html        关于
                             └─ static/           静态副本
```

### 源文件对照

| 源文件 | 关键现状 | 影响到的模块 |
|--------|---------|-------------|
| `build.py:29` | Markdown 实例硬编码 `extensions=['fenced_code', 'toc', 'codehilite']` | M-07/M-08/M-09：需提取为公共配置 |
| `build.py:91` | aboutme.md 用**独立** Markdown 实例，不含新扩展 | M-07：必须提取公共配置，否则 KaTeX/Mermaid 不生效 |
| `build.py:74` | `site_title = '胤源 Blog'` 硬编码 | M-06/M-10/M-11/M-14：需 SITE_CONFIG |
| `build.py:72` | `start_year = 2021` 硬编码 | 同上 |
| `templates/base.html:13-14` | 导航链接 `style="color:#666"`，内联样式优先级 > CSS 变量 | M-01：暗色模式下"关于"链接几乎不可见 |
| `templates/base.html:21` | footer `style="text-align:center"` | M-01：需改为 class |
| `templates/base.html:6` | `<title>{{ title or site_title or 'My Blog' }}` | 全局：缺品牌分隔符 |
| `templates/post.html` | 无标签展示、无系列导航 | M-04/M-10 |
| `static/css/style.css` | 所有颜色硬编码为 hex，无变量体系 | M-01 |

### 核心约束

- **纯静态**，无后端/数据库
- **build.py 是唯一生成逻辑**，所有产物一次性生成
- **当前 front matter 仅有**：`title`, `date`, `slug`
- **当前 dependencies**：Jinja2, Markdown, python-frontmatter, Pygments
- **CI/CD**：`deploy.yml` 自动 `pip install -r requirements.txt`，新增依赖即自动安装

---

## 二、前置准备 ✅ 已完成

状态说明：SITE_CONFIG + COMMON_MD_EXT/CFG + draft过滤 + linenums + 阅读时间估算已在 build.py 中实施。所有后续模块统一引用 SITE_CONFIG。

> **状态：已完成** — SITE_CONFIG + COMMON_MD_EXT/CFG 已在 build.py 中实施。所有后续模块引用 SITE_CONFIG[domain]，不再散落硬编码。

### 站点全局配置

在 `build.py` 顶部添加 `SITE_CONFIG`：

```python
SITE_CONFIG = {
    'domain': '691407323.github.io',
    'title': '胤源 Blog',
    'start_year': 2021,
    'author': '胤源',
    'description': '极简静态博客，Markdown 写作，Python 构建',
}
```

后续所有模块的路由、RSS、SEO 统一引用 `SITE_CONFIG[...]`，不再硬编码。

### Markdown 公共配置（解决 aboutme.md 不继承新扩展）

当前 `load_posts`（L29）和 aboutme 渲染（L91）各自创建独立的 `markdown.Markdown()` 实例。如果未来 KaTeX/Mermaid 只改了 L29 的实例，aboutme.md 不会生效。

提取公共配置：

```python
COMMON_MD_EXT = ['fenced_code', 'toc', 'codehilite']
COMMON_MD_CFG = {
    'toc': {'title': '', 'toc_depth': 3},
    'codehilite': {'linenums': False, 'css_class': 'highlight'}
}
# 后续扩展追加：'pymdownx.arithmatex', MermaidExtension()
```

两处实例改为：

```python
md = markdown.Markdown(extensions=COMMON_MD_EXT, extension_configs=COMMON_MD_CFG)
```

---

## 三、Stage 1：核心体验 ✅ 已完成

M-01 暗色模式 + M-02 代码复制 + M-03 阅读时间，约 2h 投入完成。

> M-01 暗色模式 + M-02 代码复制 + M-03 阅读时间，约 2h 投入完成。
> 依赖：#0 前置准备

### M-01：暗色模式

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐⭐⭐ 开发者刚需 |
| 工作量 | ~1h |
| 改动 | CSS 变量体系 + base.html class 重构 + theme.js |
| **状态** | ✅ 已完成（Stage 1） |

#### 关键问题：内联样式优先级

`base.html` 的 `style="color:#666"`、`style="text-align:center"` 等内联样式优先级高于 CSS 变量和 class，暗色模式下这部分颜色**不会自动切换**。必须将颜色相关的内联 style 改为 class 或 CSS 变量。

#### base.html 内联 style 改造清单

| 当前（行号） | 改造方案 | 原因 |
|-------------|---------|------|
| L11: `style="padding-left:60px; padding-right:60px; position:relative; display:flex; justify-content:center; align-items:center;"` | 改 `class="header-inner"`，`position/display/justify/align/padding` 不变，可保留 | 布局属性不受暗色模式影响 |
| L12: `style="position:absolute; left:0; display:flex; gap:8px; align-items:center;"` | 改 `class="nav-left"` | 布局属性，同上 |
| L13-14: `style="text-decoration:none; padding:8px 12px;"` + `style="color:#666;"` | 改 `class="nav-link"` | **color:#666 必须改为 CSS 变量** |
| L16: `style="text-decoration:none; color:inherit;"` | 保留 `color:inherit`（继承 body color，随主题切换）| 可保留 |
| L21: `style="text-align:center;"` | 改 `class="footer-text"` | footer 颜色需随主题变化 |

#### CSS 变量体系（style.css 顶部追加）

```css
:root {
  --bg-primary: #f9f9f9;
  --text-primary: #222;
  --text-secondary: #666;
  --border-color: #eee;
  --code-bg: #222;
  --code-text: #eee;
  --toc-bg: #fff;
  --toc-border: #e0e0e0;
  --hover-bg: #f0f0f0;
  --tag-bg: #f0f0f0;
  --tag-color: #333;
}

[data-theme="dark"] {
  --bg-primary: #1a1a2e;
  --text-primary: #e0e0e0;
  --text-secondary: #888;
  --border-color: #333;
  --code-bg: #16213e;
  --code-text: #eee;
  --toc-bg: #1a1a2e;
  --toc-border: #333;
  --hover-bg: #2a2a4a;
  --tag-bg: #333;
  --tag-color: #e0e0e0;
}
```

#### Header class 体系（base.html）

```html
<div class="header-inner">           <!-- 替代 inline style -->
  <div class="nav-left">             <!-- 替代 inline style -->
    <a href="/" class="nav-link">首页</a>
    <a href="/about.html" class="nav-link">关于</a>
    <span class="nav-divider"></span>
    <a href="/tags.html" class="nav-link">标签</a>     <!-- Stage 2 -->
    <a href="/archive.html" class="nav-link">归档</a>  <!-- Stage 2 -->
    <span class="nav-divider"></span>
    <a href="/search.html" class="nav-link">🔍</a>     <!-- Stage 4 -->
    <button id="theme-toggle" class="nav-link">🌙</button>
  </div>
  <h1 style="margin:0;"><a href="/" style="text-decoration:none; color:inherit;">...</a></h1>
</div>
```

```css
.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  padding: 8px 10px;
  font-size: 0.9rem;
}
.nav-link:hover {
  color: var(--text-primary);
  background: var(--hover-bg);
  border-radius: 4px;
}
.nav-divider {
  width: 1px; height: 16px;
  background: var(--border-color);
  margin: 0 2px; align-self: center;
}
.footer-text {
  text-align: center;
  color: var(--text-secondary);
}
```

#### theme.js（新增 `static/js/theme.js`）

包含暗色切换 + Mermaid 主题同步（为 M-09 预留回调）。

```javascript
(function() {
  const KEY = 'blog-theme';
  const root = document.documentElement;

  function init() {
    const saved = localStorage.getItem(KEY);
    if (saved) { root.setAttribute('data-theme', saved); return saved; }
    const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', dark ? 'dark' : 'light');
    return dark ? 'dark' : 'light';
  }

  const current = init();
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.textContent = current === 'dark' ? '☀️' : '🌙';
    btn.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem(KEY, next);
      btn.textContent = next === 'dark' ? '☀️' : '🌙';
      // M-09: Mermaid 主题同步
      if (typeof mermaid !== 'undefined' && mermaid.run) {
        mermaid.run({ theme: next === 'dark' ? 'dark' : 'default' });
      }
    });
  }
  // 跟随系统偏好（未手动选择时）
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (!localStorage.getItem(KEY)) {
      root.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      if (btn) btn.textContent = e.matches ? '☀️' : '🌙';
    }
  });
})();
```

⚠️ Mermaid 初始加载时设 `theme: 'default'`，切换时由上述回调更新。

#### 现有 CSS 修改（style.css）

硬编码颜色 → CSS 变量替换：

| 原值 | 替换 |
|------|------|
| `background: #f9f9f9` (body, html) | `var(--bg-primary)` |
| `color: #222` | `var(--text-primary)` |
| `color: #666` (.post-meta, .toc-sidebar a) | `var(--text-secondary)` |
| `border-bottom: 1px solid #eee` | `1px solid var(--border-color)` |
| `.toc-sidebar { background: #fff }` | `var(--toc-bg)` |
| `.toc-sidebar { border-right: 1px solid #e0e0e0 }` | `var(--toc-border)` |

`pre { background:#222; color:#eee }` 代码块建议始终深色，暂不跟随主题切换。

---

### M-02：代码块一键复制

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐⭐ 开发者高频操作 |
| 工作量 | ~30min |
| 改动 | 新增 `static/js/code-copy.js` + CSS |
| **状态** | ✅ 已完成（Stage 1） |

**关键**：移动端无 `hover`，需用 `@media (hover: none)` 保证按钮始终可见。

```css
.code-copy-btn {
  position: absolute; top: 6px; right: 6px;
  padding: 3px 10px; font-size: 12px;
  background: rgba(255,255,255,0.15);
  color: var(--code-text);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 4px; cursor: pointer;
  opacity: 0.3;
  transition: opacity 0.2s, background 0.2s;
}
.codehilite:hover .code-copy-btn { opacity: 1; }
@media (hover: none) {
  .code-copy-btn { opacity: 0.4; }
  .codehilite:active .code-copy-btn { opacity: 1; }
}
.code-copy-btn:hover {
  background: rgba(255,255,255,0.25);
}
```

JS 含 Clipboard fallback（file:// 协议兼容）：

```javascript
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.codehilite').forEach(block => {
    const btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.textContent = '复制';
    btn.setAttribute('aria-label', '复制代码');
    btn.addEventListener('click', async () => {
      const code = block.querySelector('code');
      if (!code) return;
      try {
        await navigator.clipboard.writeText(code.textContent);
      } catch (_) {
        const ta = document.createElement('textarea');
        ta.value = code.textContent;
        ta.style.cssText = 'position:fixed;opacity:0;left:-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      btn.textContent = '已复制 ✓';
      setTimeout(() => btn.textContent = '复制', 2000);
    });
    block.style.position = 'relative';
    block.appendChild(btn);
  });
});
```

---

### M-03：阅读时间估算

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐ 小投入信息密度提升 |
| 工作量 | ~15min |
| 改动 | `build.py` 新函数 + `post.html` 展示 |
| **状态** | ✅ 已完成（Stage 1） |

```python
def estimate_read_time(html_content):
    text = re.sub(r'<[^>]+>|\s+', '', html_content)
    # CJK 统一汉字 + 扩展A + 常用全角标点（不含全角ASCII数字/片假名）
    cn = len(re.findall(r'[一-鿿㐀-䶿！？　-〿]', text))
    en = len(re.findall(r'[a-zA-Z]+', text))
    minutes = cn / 400 + en / 200
    return '< 1 分钟' if minutes < 1 else f'{int(minutes)} 分钟'
```

`post.html`：`<p class="post-meta">{{ post.date }} · 阅读 {{ post.read_time }}</p>`

---

## 四、Stage 2：博客导航 ✅ 已完成

M-04 标签系统 + M-05 归档页 + M-06 RSS Feed + M-14 SEO Meta 全部完成。M-07 front matter 拓展已整合到 #0 前置准备。

> M-04 标签系统 + M-05 归档页 + M-06 RSS Feed + M-14 SEO Meta 全部完成。
> 注意：M-07 front matter 拓展已整合到 #0 前置准备中（tags/draft/linenums/description 字段已在 load_posts 中处理）。

### M-07：front matter 拓展字段

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐ 所有后续模块的数据基础 |
| 工作量 | ~20min |
| 改动 | `build.py`（提取公共 MD 配置 + draft 过滤 + linenums 实现） |
| **状态** | ✅ 已完成（#0 前置准备） |

新增字段：

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `tags` | 否 | 数组 / 逗号字符串 | 文章标签 |
| `draft` | 否 | 布尔 | `true` 跳过构建 |
| `description` | 否 | 字符串 | 文章摘要 |
| `cover` | 否 | 字符串 | 封面图片路径 |
| `updated` | 否 | 日期 | 最后修改日期 |
| `linenums` | 否 | 布尔 | 该篇是否显示代码行号 |

**linenums 实现**（原方案遗漏）：

```python
linenums = meta.get('linenums', False)
md = markdown.Markdown(
    extensions=COMMON_MD_EXT,
    extension_configs={**COMMON_MD_CFG, 'codehilite': {'linenums': linenums}}
)
```

**Draft 过滤**：分离 draft_posts 和 normal_posts，只构建 normal_posts。Draft 不计入标签/归档/RSS 计数。

---

### M-04：文章标签/分类系统

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐⭐⭐ 无分类体系，文章无法按主题浏览 |
| 工作量 | ~1.5h |
| 改动 | `build.py` + 2 模板 + CSS + header 导航 |
| **状态** | ✅ 已完成（Stage 2） |

依赖：M-07（tags 字段）已先完成。

#### 数据结构

front matter：
```yaml
tags: [tstl, luascript, compiler]
# 兼容字符串：tags: "tstl, compiler"
```

#### 关键修正

1. **`{% endblock %}` 语法**（原方案漏了 `%`）
2. **中文标签 URL 编码**：`urllib.parse.quote(tag)` 编码后存 URL，显示用原始名
3. **post.html 需要 tags_list 和 all_tag_url_map**（标签页链接所需映射）

#### 模板

`templates/tags.html`：标签云（flex wrap）+ 按标签分组折叠列表

`templates/tag.html`：单标签文章列表

#### CSS 新增

```css
.tag-cloud { display: flex; flex-wrap: wrap; gap: 8px 12px; }
.tag-item {
  padding: 4px 12px; border-radius: 4px;
  background: var(--tag-bg); color: var(--tag-color);
  text-decoration: none; font-size: 0.9rem;
}
.tag-item small { color: var(--text-secondary); }
```

⚠️ 使用 `--tag-bg` / `--tag-color` 变量而非硬编码颜色，避免与 M-01 的 hover 背景撞色。

#### post.html 展示标签

在 `</article>` 前加入标签展示区：

```html
{% if post.tags_list %}
<div class="post-tags" style="margin-top:16px; display:flex; gap:8px; flex-wrap:wrap; padding-top:16px; border-top:1px solid var(--border-color);">
  {% for tag in post.tags_list %}
  <a href="/tags/{{ all_tag_url_map.get(tag, tag) }}.html"
     class="tag-inline"
     style="padding:2px 8px; background:var(--tag-bg); color:var(--tag-color);
            text-decoration:none; border-radius:4px; font-size:0.85rem;">
    {{ tag }}
  </a>
  {% endfor %}
</div>
{% endif %}
```

---

### M-05：文章归档页

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐ 时间维度导航 |
| 工作量 | ~30min |
| 改动 | `build.py` + `templates/archive.html` |
| **状态** | ✅ 已完成（Stage 2） |

```python
from collections import defaultdict
archive = defaultdict(list)
for p in posts:
    date_str = p['meta'].get('date', '')
    if not date_str: continue       # ← 无日期文章不入归档
    archive[date_str[:4]].append({...})
archive = dict(sorted(archive.items(), reverse=True))
```

---

### M-06：RSS/Atom Feed

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐⭐ 博客标配 |
| 工作量 | ~30min |
| 改动 | `build.py` + `templates/feed.xml` |
| **状态** | ✅ 已完成（Stage 2） |

使用 `SITE_CONFIG['domain']` 统一域名。

```xml
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{{ site_title }}</title>
  <link href="https://{{ site_domain }}/feed.xml" rel="self"/>
  <link href="https://{{ site_domain }}/"/>
  <updated>{{ current_date }}</updated>
  <author><name>{{ site_title }}</name></author>
  <id>https://{{ site_domain }}/</id>
  {% for p in posts %}
  <entry>
    <title>{{ p.title }}</title>
    <summary>{{ p.description or p.title }}</summary>
    <link href="https://{{ site_domain }}/posts/{{ p.slug }}.html"/>
    <id>https://{{ site_domain }}/posts/{{ p.slug }}.html</id>
    <updated>{{ p.date }}T00:00:00Z</updated>
    <content type="html">{{ p.content \| safe }}</content>
  </entry>
  {% endfor %}
</feed>
```

`current_date` 生成：`datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')`

base.html 加 RSS 链接：`<link rel="alternate" type="application/atom+xml" title="{{ site_title }}" href="/feed.xml">`

---

## 五、Stage 3：内容表达 ✅ 已完成

M-08 KaTeX + M-09 Mermaid + M-10 系列导航全部完成。

> M-08 KaTeX + M-09 Mermaid + M-10 系列导航全部完成。

### M-08：KaTeX 数学公式

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐⭐ 算法/统计学刚需 |
| 工作量 | ~45min |
| 改动 | `build.py`（加 pymdownx）+ base.html（KaTeX CDN） |
| **状态** | ✅ 已完成（Stage 3） |

**关键决策**：放弃 `$` 行内分隔符（与普通文本`$HOME`冲突），只用 `\(...\)` 和 `\[...\]` + `$$...$$`。

```python
# build.py extensions
md = markdown.Markdown(
    extensions=COMMON_MD_EXT + ['pymdownx.arithmatex'],
    extension_configs={**COMMON_MD_CFG, 'pymdownx.arithmatex': {'generic': True}}
)
```

base.html 引入 KaTeX CDN（auto-render 方案）：

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script defer>
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof renderMathInElement === 'function') {
      renderMathInElement(document.body, {
        delimiters: [
          {left: '$$', right: '$$', display: true},
          {left: '\\(', right: '\\)', display: false},
          {left: '\\[', right: '\\]', display: true}
        ],
        throwOnError: false
      });
    }
  });
</script>
```

使用示例：`$$P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}$$` / `\(E = mc^2\)`

---

### M-09：Mermaid 图表

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐⭐ 架构图/流程图刚需 |
| 工作量 | ~1h |
| 改动 | `build.py` 自定义扩展 + base.html CDN |
| **状态** | ✅ 已完成（Stage 3） |

**关键**：Preprocessor 优先级必须低于 fenced_code（50 < 175），否则 ` ```mermaid ` 被先处理为代码块。

```python
class MermaidPreprocessor(Preprocessor):
    def run(self, lines):
        in_m = False; result = []
        for line in lines:
            if line.strip().startswith('```mermaid'):
                in_m = True; result.append('<div class="mermaid">')
            elif in_m and line.strip() == '```':
                in_m = False; result.append('</div>')
            elif in_m: result.append(line)
            else: result.append(line)
        return result

class MermaidExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MermaidPreprocessor(md), 'mermaid', 50)
```

base.html：
```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true, theme: 'default', securityLevel: 'loose' });</script>
```
⚠️ 完整 bundle ~1.5MB。Mermaid 块内不允许嵌套代码 fence。

---

### M-10：文章系列导航

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐⭐ TSTL 系列已有系列关系但无导航 |
| 工作量 | ~1h |
| 改动 | `build.py` + `post.html` |
| **状态** | ✅ 已完成（Stage 3） |

数据结构：`series: 系列名` + `series_order: 序号`

**关键**：series_map 先在 build() 中构建完成，再进入 render loop。在 render loop 中标注 prev/next。

```python
# 构建 series_map（所有文章加载后）
series_map = {}
for p in posts:
    s = p['meta'].get('series')
    if s:
        series_map.setdefault(s, []).append({
            'title': p['meta'].get('title', ''),
            'slug': p['meta']['slug'],
            'date': p['meta'].get('date', ''),
            'series_order': p['meta'].get('series_order', 0),
        })
for s in series_map.values():
    s.sort(key=lambda x: x['series_order'])

# render loop 中标注
for p in posts:
    slug = p['meta']['slug']
    series = p['meta'].get('series')
    if series:
        sp_list = series_map[series]
        idx = next(i for i, sp in enumerate(sp_list) if sp['slug'] == slug)
        prev = sp_list[idx-1] if idx > 0 else None
        nxt = sp_list[idx+1] if idx < len(sp_list)-1 else None
        nav = {'prev': prev, 'next': nxt, 'list': sp_list, 'name': series}
    else:
        nav = None
    html = tpl.render(post=p['meta'], ..., series_nav=nav, ...)
```

post.html 系列导航区（`</article>` 下方）：

```html
{% if series_nav %}
<div class="series-nav" style="margin-top:24px; padding:16px; border:1px solid var(--border-color); border-radius:8px;">
  {% if series_nav.prev %}
  <div style="font-size:0.9rem; margin-bottom:12px;">← 上一篇：<a href="/posts/{{ series_nav.prev.slug }}.html">{{ series_nav.prev.title }}</a></div>
  {% endif %}
  <div style="font-size:0.9rem; color:var(--text-secondary); margin-bottom:8px;">系列：{{ series_nav.name }}</div>
  {% for sp in series_nav.list %}
  <a href="/posts/{{ sp.slug }}.html" class="series-item"
     style="display:block; padding:4px 0;
            color:{% if sp.slug == post.slug %}var(--text-primary); font-weight:bold;{% else %}var(--text-secondary);{% endif %}
            text-decoration:none;">
    {{ sp.series_order }}. {{ sp.title }}{% if sp.slug == post.slug %} ← 当前{% endif %}
  </a>
  {% endfor %}
  {% if series_nav.next %}
  <div style="font-size:0.9rem; margin-top:12px;">下一篇：<a href="/posts/{{ series_nav.next.slug }}.html">{{ series_nav.next.title }} →</a></div>
  {% endif %}
</div>
{% endif %}
```

`is_current` 字段冗余，模板中用 `{% if sp.slug == post.slug %}` 判断即可。

---

## 六、Stage 4：深度扩展

### M-11：站内搜索（FlexSearch）

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐⭐ 文章 > 20 篇后显著提升 |
| 工作量 | ~1.5h |
| 改动 | `build.py` + `templates/search.html` + `static/js/search.js` |
| **状态** | ✅ 已完成（Stage 4） |

**关键**：FlexSearch CDN 仅在搜索页加载，不放入 base.html。base.html 加 `{% block extra_scripts %}{% endblock %}` 空块。

`search.html`：
```html
{% extends "base.html" %}
{% block content %}
<main class="container">
  <h2>搜索文章</h2>
  <div style="position:relative; margin-top:16px;">
    <input id="search-input" type="search" placeholder="关键词..."
           style="width:100%; padding:12px; font-size:16px;
                  border:1px solid var(--border-color);
                  background:var(--bg-primary); color:var(--text-primary);
                  box-sizing:border-box;">
    <span id="search-status" style="position:absolute; right:12px; top:14px; color:var(--text-secondary);"></span>
  </div>
  <div id="search-results" style="margin-top:16px;"></div>
</main>
{% endblock %}
{% block extra_scripts %}
<script src="https://cdn.jsdelivr.net/npm/flexsearch@0.7.31/dist/flexsearch.bundle.min.js"></script>
<script src="/static/js/search.js"></script>
{% endblock %}
```

完整 `search.js`（防抖 + 标题优先排序 + Enter 跳转）：

```javascript
let idxObj = null;
async function loadIndex() {
  const res = await fetch('/search-index.json');
  const data = await res.json();
  const idx = new FlexSearch.Index({ tokenize: 'forward', resolution: 9 });
  data.forEach(d => idx.add(d.slug, d.title + ' ' + d.content));
  return { idx, data };
}
function renderResults(results, data, el) {
  if (!results.length) { el.innerHTML = '<p style="color:var(--text-secondary)">未找到</p>'; return; }
  el.innerHTML = results.map(slug => {
    const d = data.find(x => x.slug === slug);
    return `<article class="post" style="padding:16px 0; border-bottom:1px solid var(--border-color);">
      <h3><a href="/posts/${d.slug}.html" style="color:var(--text-primary); text-decoration:none;">${d.title}</a></h3>
      <p class="post-meta">${d.date}${d.tags.length ? ' · ' + d.tags.join(', ') : ''}</p>
      <p style="color:var(--text-secondary);">${d.excerpt}...</p>
    </article>`;
  }).join('');
}
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

document.addEventListener('DOMContentLoaded', async () => {
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  if (!input) return;
  try { idxObj = await loadIndex(); } catch(_) {
    results.innerHTML = '<p style="color:#c00;">索引加载失败，请刷新</p>'; return;
  }
  const doSearch = debounce(q => {
    const qTrim = q.trim();
    if (!qTrim) { results.innerHTML = ''; status.textContent = ''; return; }
    const r = idxObj.idx.search(qTrim);
    status.textContent = `${r.length} 条结果`;
    // 标题命中优先
    const titleHits = r.filter(s => { const d = idxObj.data.find(x => x.slug === s); return d && d.title.toLowerCase().includes(qTrim.toLowerCase()); });
    renderResults([...titleHits, ...r.filter(s => !titleHits.includes(s))], idxObj.data, results);
  }, 200);
  input.addEventListener('input', e => doSearch(e.target.value));
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') { const r = idxObj.idx.search(input.value.trim()); if (r.length) location.href = '/posts/' + r[0] + '.html'; }
  });
});
```

---

### M-12：评论系统（Giscus）

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐ GitHub 用户直接评论 |
| 工作量 | ~20min |
| 改动 | 仅 `post.html` |
| **状态** | ✅ 已完成（Stage 4） |

⚠️ **保持 `data-mapping="pathname"`**（而非 review 建议的 title）。pathname 唯一，title 可能冲突。

```html
<section style="max-width:800px; margin:32px auto; padding:0 24px;">
  <h3 style="border-top:1px solid var(--border-color); padding-top:24px;">评论</h3>
  <script src="https://giscus.app/client.js"
          data-repo="你的用户名/仓库名"
          data-repo-id="..."
          data-category="Announcements"
          data-category-id="..."
          data-mapping="pathname"
          data-strict="0"
          data-reactions-enabled="1"
          data-emit-metadata="0"
          data-input-position="bottom"
          data-theme="preferred_color_scheme"
          data-lang="zh-CN"
          crossorigin="anonymous"
          async></script>
</section>
```

---

### M-13：图片优化（WebP + 缩略图） ✅ 已完成

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐ 图片是最大加载瓶颈 |
| 工作量 | ~2.5h |
| 改动 | `build.py` + Pillow 依赖 + `static/images/` 目录 |
| 状态 | ✅ 已完成：`process_images()` 软依赖 Pillow，未装自动跳过；增量跳过未更新图；主图限宽 1600、缩略图 480、quality=82。实测 468KB PNG→56.7KB WebP（-88%） |

新增依赖：`Pillow>=10.0`

**关键决策**：只转 WebP，不保留原始格式。WebP 兼容率 95%+，读者群体浏览器版本普遍较新。

**关键决策**：Markdown 图片引用**不自动替换**，强制写作者使用 `/static/images/` 绝对值路径。路径映射逻辑复杂且不可靠。

```python
from PIL import Image

IMG_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
MAX_IMG_DIM = 4000

def process_images(src_root, out_root):
    for img_dir in [src_root / 'content' / 'images', src_root / 'static' / 'images']:
        if not img_dir.exists(): continue
        for img_path in img_dir.rglob('*'):
            if img_path.suffix.lower() not in IMG_EXTS: continue
            rel = img_path.relative_to(img_dir)
            out_dir = out_root / 'static' / 'images' / rel.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            webp_path = out_dir / (rel.stem + '.webp')
            thumb_path = out_dir / (rel.stem + '-thumb.webp')

            try:
                with Image.open(img_path) as im:
                    w, h = im.width, im.height
                    # 尺寸上限
                    if max(w, h) > MAX_IMG_DIM:
                        scale = MAX_IMG_DIM / max(w, h)
                        im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
                        w, h = im.width, im.height
                    # WebP 原图（一次打开，两处使用）
                    im.save(webp_path, 'WEBP', quality=80)
                    # 缩略图 200px 宽（复用同一 image 对象）
                    tw, th = 200, int(h * 200 / w)
                    im.resize((tw, th), Image.LANCZOS).save(thumb_path, 'WEBP', quality=75)
            except Exception as e:
                print(f'跳过: {img_path.name} ({e})')
                continue
```

写作规范：Markdown 中图片引用 `![alt](/static/images/xxx.webp)`。

---

### M-14：Open Graph / SEO Meta

| 项 | 内容 |
|------|------|
| 价值 | ⭐⭐ 社交分享 + 搜索引擎收录 |
| 工作量 | ~15min |
| 改动 | 仅模板（base.html + post.html / index.html render call） |
| **状态** | ✅ 已完成（Stage 2） |

**关键**：`og:image` 条件输出——有图片才声明，没有让平台自动抓取。

```html
<!-- base.html head -->
<meta name="description" content="{{ description or site_description }}">
<meta name="author" content="{{ site_author }}">
<link rel="canonical" href="{{ canonical_url }}">
<meta property="og:type" content="{{ og_type or 'website' }}">
<meta property="og:title" content="{{ og_title or title or site_title }}">
<meta property="og:description" content="{{ og_description or description or site_description }}">
<meta property="og:url" content="{{ canonical_url }}">
{% if og_image %}<meta property="og:image" content="{{ og_image }}">{% endif %}
<meta name="twitter:card" content="summary_large_image">
```

各页面 `og:type`：首页=`website`，文章页=`article`。

`<title>` 改进：文章页 `TSTL 插件架构 · 胤源 Blog`，首页 `胤源 Blog`。

---

## 七、实施路线

### 实施顺序

| # | 模块 | 阶段 | 工作量 | 前置依赖 |
|---|------|------|--------|---------|
| 0 | **前置** SITE_CONFIG + COMMON_MD | — | 5min | 无 | ✅ 已完成 |
| 1 | M-07 front matter 拓展 | #0 前置 | 20min | 无 | ✅ 已完成 | ✅ 已完成 |
| 2 | M-01 暗色模式 | Stage 1 | 1h | #0 | ✅ 已完成 | ✅ 已完成 |
| 3 | M-02 代码复制 | Stage 1 | 30min | 无 | ✅ 已完成 | ✅ 已完成 |
| 4 | M-03 阅读时间 | Stage 1 | 15min | 无 | ✅ 已完成 | ✅ 已完成 |
| 5 | M-04 标签系统 | Stage 2 | 1.5h | #1 | ✅ 已完成 | ✅ 已完成 |
| 6 | M-05 归档页 | Stage 2 | 30min | #1 | ✅ 已完成 | ✅ 已完成 |
| 7 | M-06 RSS Feed | Stage 2 | 30min | #0, #1 | ✅ 已完成 | ✅ 已完成 |
| 8 | M-08 KaTeX | Stage 3 | 45min | #0 | ✅ 已完成 | ✅ 已完成 |
| 9 | M-09 Mermaid | Stage 3 | 1h | #0, #2（M-01 主题同步） | ✅ 已完成 | ✅ 已完成 |
| 10 | M-10 系列导航 | Stage 3 | 1h | 无 | ✅ 已完成 | ✅ 已完成 |
| 11 | M-11 搜索 | Stage 4 | 1.5h | #0 | ✅ 已完成 | ✅ 已完成 |
| 12 | M-12 Giscus | Stage 4 | 20min | 无 | ✅ 已完成 | ✅ 已完成 |
| 13 | M-13 图片优化 | Stage 4 | 2.5h | Pillow 依赖 | 待实施 → ✅ 已完成 |
| 14 | M-14 SEO Meta | Stage 4 | 15min | #0 | ✅ 已完成 |

### 推荐节奏

```
Day 1: 前置（SITE_CONFIG + COMMON_MD）+ M-07（front matter）
        → 建立数据基础

Day 2: M-01（暗色模式）+ M-02（代码复制）
        → Stage 1 核心体验

Day 3: M-03（阅读时间）+ M-04（标签）+ M-05（归档）+ M-06（RSS）
        → Stage 2 完整导航

Day 4: M-08（KaTeX）+ M-09（Mermaid）+ M-10（系列导航）
        → Stage 3 内容表达

Week 2+: M-11/12/13/14 按需启动
```

---

## 八、注意事项

### 跨模块依赖链

```
前置（SITE_CONFIG + COMMON_MD）
  ├── M-07（front matter 拓展）──→ M-04（标签）──→ M-04 post.html 展示
  ├── M-06/M-10/M-11/M-14（需要 SITE_CONFIG['domain']）
  ├── M-09（需要 COMMON_MD + M-01 theme.js 回调）
  └── M-11（base.html extra_scripts 块）
```

### CSS 变量覆盖内联样式

内联 `style="color:#666"` 优先级 > CSS class/variable。M-01 必须将所有颜色内联改为 class，否则暗色模式无效。

### CDN 体积

| 库 | 体积 | 加载方式 |
|------|------|---------|
| KaTeX CSS + JS | ~45KB | 全局（base.html head） |
| Mermaid full bundle | ~1.5MB | 全局（base.html head） |
| FlexSearch | ~10KB | **仅搜索页**（search.html extra_scripts） |

建议 Mermaid 后续可改为按需加载（仅含 Mermaid 图表的页面）。

### 中文搜索

FlexSearch `tokenize: 'forward'` 对中文按字符正向索引，精度一般。适合关键词搜索，不适合语义搜索。后续可升级拼音分词。

### 图片路径规范

WebP 转换后，Markdown 中的图片路径**不会自动替换**。必须手动写 `![alt](/static/images/xxx.webp)`。

### 兼容性

| 场景 | 状态 |
|------|------|
| WebP | 95%+ 浏览器支持，Safari 14+ 全支持 |
| Clipboard API | HTTPS/localhost 可用，file:// 用 execCommand fallback |
| FlexSearch CDN | 仅搜索页加载，不影响其他页面 |
| Giscus | 需 GitHub Discussions 已启用 |
| KaTeX auto-render | 需浏览器支持 deferred script |

### Git Commit 策略

每个模块一个 commit，前缀分类：

```
feat: 暗色模式 — CSS 变量体系 + 主题切换
feat: 代码块一键复制按钮
feat: 文章阅读时间估算（CJK 范围修正）
feat: front matter 拓展字段（tags/draft/description/linenums）
feat: 标签/分类系统（URL编码 + post.html 标签展示）
feat: 文章归档页（按年份分组）
feat: RSS/Atom Feed 订阅源（SITE_CONFIG 统一域名）
feat: KaTeX 公式渲染（放弃 $ 分隔符）
feat: Mermaid 图表（preprocessor 优先级 50）
feat: 文章系列导航（prev/next 链接）
feat: 站内搜索（FlexSearch + 按需加载）
feat: Giscus 评论系统（pathname 映射）
feat: 图片 WebP 压缩 + 缩略图（Pillow）
feat: Open Graph / SEO Meta 标签
```

---

*最后更新：2026-07-03*
*状态：规划完成，已做两轮审查修正*
