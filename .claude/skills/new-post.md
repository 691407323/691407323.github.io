---
name: new-post
description: 将用户输入的文字或文件内容生成为符合博客格式的 Markdown 文章。直接描述需求或提供文件路径即可，例如"帮我把这段文字生成一篇博客"或"把 xxx.md 变成博客文章"。
---

## 触发方式

直接对 Claude 说"生成一篇博客文章"、"把这段内容写成博客"或直接粘贴文件路径，无需使用任何斜杠命令。

## 站点能力速览（写文章时据此选用语法）

| 能力 | 是否支持 | 写法 | 说明 |
|------|---------|------|------|
| 代码块 + 语法高亮 | ✅ | ` ```python ` … ` ``` ` | 自动高亮，`<code class="language-xxx">` |
| 代码行号 | ✅ | front matter 加 `linenums: true` | 逐篇控制 |
| 目录 TOC | ✅ | 自动按标题生成 | 深度 3 级 |
| 脚注 | ✅ | `[^1]` + `[^1]: 内容` | 渲染到页面底部 |
| 数学公式（KaTeX） | ✅ | 块级 `$$...$$` / 行内 `\(...\)` | **不用** `$...$`（与文本冲突） |
| Mermaid 图表 | ✅ | ` ```mermaid ` … ` ``` ` | 流程图/架构图 |
| HTML 内嵌 | ✅ | `<details>`、`<kbd>`、`<a>` 等 | 原生标签可直接写 |
| 图片 | ✅ | `![alt](/static/images/x.webp)` | **绝对路径**，自动转 WebP |
| 标签 tags | ✅ | front matter `tags: [a, b]` | 支持数组或逗号字符串 |
| 封面 og:image | ✅ | front matter `cover: static/images/x.png` | 不带前导斜杠 |
| 系列导航 | ✅ | front matter `series` + `series_order` | 上一篇/下一篇 |
| 删除线 `~~` | ❌ | — | 未启用 `pymdownx.tilde`，改用 HTML `<s>` |
| 任务列表 `- [ ]` | ❌ | — | 未启用 `pymdownx.tasklist`，改用 HTML `<input type=checkbox>` |
| Markdown 表格 `\|` | ❌ | — | 未启用 `tables` 扩展，改用 HTML `<table>` |

> **图片处理**：构建时 `static/images/` 里的 PNG/JPG 会自动生成同名 `.webp`（限宽 1600px）+ `_thumb.webp` 缩略图。文中建议引用已生成的 `.webp` 省体积，原始 PNG 也保留可用。

## 处理流程

1. **接收输入**：用户提供文字内容、文件路径（单个或多个），或两者混合
2. **识别文件路径**：
   - 路径特征：包含扩展名（尤其是 `.md`）、`/` 或 `\` 分隔符、以 `./` 或盘符开头
   - 正文中引用路径（如"参考 xxx.md 的格式"）不视为文件路径，只有用户意图读取文件时才识别
   - 无法确定时，向用户确认
3. **读取内容**：
   - 若输入是文件路径，读取文件内容
   - 若文件不存在或读取失败，提示用户并停止
   - 若输入为空，提示用户补充内容并停止
4. **提取标题**：
   - 优先级：文件名（去掉 .md 后缀） > 内容第一行非空文本 > 默认"未命名文章"
   - 若第一行是 Markdown 标题标记 `# xxx`，提取 `xxx` 作为标题
   - 若内容为空，使用默认标题
   - **标题精简规则**：
     - 标题应**精简准确**，用最短的文字概括内容核心，去除冗余修饰词
     - 英文术语在长度较长时优先使用**大写缩写**（如 `TypeScriptToLua` → `TSTL`，`JavaScript` → `JS`）
     - 常见缩写对照：`TypeScript` → `TS`, `JavaScript` → `JS`, `TypeScriptToLua` → `TSTL`, `Configuration` → `Config`, `Documentation` → `Docs`, `Development` → `Dev`, `Application` → `App`, `Implementation` → `Impl`
     - 中文标题尽量控制在 15 字以内，英文缩写按大写字母计
5. **提取日期**（按优先级）：
   - 从文件名中提取（如 `2026-05-28-docker.md` → `2026-05-28`）
   - 从原文 front matter 的 `date` 字段提取
   - 以上都无法提取时，使用当前日期
6. **生成 slug**（纯英文，不含中文）：
   - 基于精简后的标题生成
   - **必须只包含小写字母、数字、连字符 `-`，不得出现中文字符**
   - 中文/英文混合标题：中文部分译为英文或音译，或全部删除
   - 示例：`TSTL 插件架构` → `tstl-plugin-architecture`
   - 英文/数字：小写，空格替换为连字符，去除特殊字符（仅保留字母、数字、连字符）
   - 若目标文件已存在，追加编号：`slug.md` → `slug-2.md` → `slug-3.md`
7. **处理 front matter**：
   - 若原文已有 front matter（`---` 包裹的元数据），保留原文中的字段，仅覆盖 `title`/`date`/`slug`
   - 若原文无 front matter，按标准格式生成
   - **可选字段**（按需补充，参见下表，不要硬塞不相关字段）：
     - `tags: [标签1, 标签2]` — 数组或逗号字符串
     - `description: 一句话摘要` — 用于 RSS summary、SEO description
     - `draft: true` — 草稿，跳过构建（不计入标签/归档/RSS）
     - `linenums: true` — 该篇代码块显示行号
     - `cover: static/images/xxx.png` — 封面图（**不带前导斜杠**），生成 og:image
     - `updated: 2026-07-04` — 最后修改日期，文章页显示"更新于"，RSS 优先使用
     - `series: 系列名` + `series_order: 2` — 系列导航（按 series_order 升序排列）
8. **保存文件**：写入 `content/posts/<slug>.md`
9. **通知用户**：报告生成的文件路径、标题和日期来源

> **提示**：`build.py` 会自动扫描 `content/posts/` 目录下的所有 `.md` 文件，新文章无需手动注册，构建时自动包含。`slug` 不可重复，重复构建会报错。

## Front Matter 字段表

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `title` | 否 | 字符串 | 文章标题，默认取文件名 |
| `date` | 否 | 日期(YYYY-MM-DD) | 发布日期，用于排序降序 |
| `slug` | 否 | 字符串 | URL 标识，默认取文件名，**不可重复** |
| `tags` | 否 | 数组/逗号字符串 | 文章标签 |
| `description` | 否 | 字符串 | 摘要（RSS/SEO） |
| `draft` | 否 | 布尔 | `true` 跳过构建 |
| `linenums` | 否 | 布尔 | 该篇代码块显示行号 |
| `cover` | 否 | 字符串 | 封面图路径（不带前导斜杠），生成 og:image |
| `updated` | 否 | 日期 | 最后修改日期 |
| `series` | 否 | 字符串 | 系列名 |
| `series_order` | 否 | 数字 | 系列内序号 |

## 多文件处理

- 若用户一次提供多个文件路径，**依次生成多篇独立文章**
- 每篇使用各自的文件名和内容
- 逐个报告结果，不合并为单篇

## 格式要求

- Front matter 必须包含 `title`、`date`、`slug`
- 保留原文 front matter 中的自定义字段（tags、description、series 等）
- 正文保持原文结构和格式，不做内容删减
- 支持代码块、引用、脚注、公式、Mermaid 等 Markdown 语法
- 图片用绝对路径 `/static/images/xxx.webp`（或 `.png`）

## 图片处理

1. 把图片放进 `static/images/`（构建时自动生成 `.webp` + `_thumb.webp`）
2. 正文用绝对路径引用：`![alt](/static/images/xxx.webp)`
3. 封面图用 front matter `cover: static/images/xxx.png`（不带前导斜杠，会拼成绝对 URL 生成 og:image）
4. 自适应已内置：`.post-body img { max-width:100% }`，无需手控宽度

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 文件路径不存在 | 提示"文件不存在：xxx"，请用户检查路径 |
| 文件读取失败 | 提示"无法读取文件：xxx"，列出可能原因 |
| 输入内容为空 | 提示"内容为空，请提供文字内容或文件路径" |
| slug 冲突 | 自动追加编号（slug-2、slug-3...） |
| 无写入权限 | 提示"无法写入 content/posts/ 目录，请检查权限" |

## 跨页面跳转链接

当文章内容包含多个章节、附录、目录树等结构，需要实现跳转链接时，按以下规则生成。

### 锚点生成规则

使用 python-markdown 的 `toc` 扩展算法：标题文本 **小写**，非字母数字替换为 `-`，去除首尾 `-`。

示例：
- `### 1. lua-winhelp — Windows 控制台输入模块` → `#1-lua-winhelp-windows`
- `## 附录：Windows 控制台输入模块 lua-winhelp.c` → `#windows-lua-winhelpc`

### 目录树锚点声明

目录树通常放在 `<pre>` 块中，代码块内的 Markdown 链接语法不会渲染为链接，需使用 HTML `<a>` 标签。给 `<pre>` 加 `id` 属性作为返回目标：

```markdown
<pre id="folder-tree">
core/
├── skynet/
├── posix/
└── pthread-win32/
cservice-src/
<a href="#1-lua-winhelp-windows" style="color:#4fc3f7;">[→ lua-winhelp]</a>
ts/
├── src/
├── tools/
└── interface/
</pre>
```

### 跳转链接格式

| 类型 | 格式 | 示例 |
|------|------|------|
| 正向跳转 | `<a href="#slug" style="color:#4fc3f7;">[→ label]</a>` | `[→ lua-winhelp]` |
| 返回跳转（独立行） | `<a href="#target-id" style="color:#4fc3f7;">[↩ label]</a>` | `[↩ 返回目录树]` |
| 返回跳转（标题同行） | 同上，加 `float:right` | 放在标题右侧 |

### 附录标题的返回链接

附录标题右侧放置返回链接。**不要将标题文字本身包裹在自引用链接中**（会导致原地跳转），标题保持纯文本。

返回链接有两种放置方式：

| 方式 | 格式 | 效果 |
|------|------|------|
| 同行内联 | `...模块 <a href="#target-id" style="color:#4fc3f7;">[↩]</a>` | `[↩]` 紧跟在标题文字后面 |
| 同行悬浮 | 同上，加 `float:right` | `[↩]` 靠右，与标题文字分离 |

```markdown
### 1. lua-winhelp.c — Windows 控制台输入模块 <a href="#folder-tree" style="color:#4fc3f7;">[↩]</a>
```

### 附录子节层级

编号附录（如 `### 1. xxx`、`### 2. xxx`）下的子节统一使用 `####`（比附录标题深一级）：

```markdown
## 附录

### 1. lua-winhelp — Windows 控制台输入模块
#### 核心设计
#### Lua 接口
#### 完整源码

### 2. 其他模块
#### 功能说明
#### 使用示例
```

### 注意事项

- `<pre>` 块内的链接使用 HTML `<a href>` 标签，不能用 Markdown 的 `[text](url)` 语法（代码块内容会被转义为纯文本）
- 所有跳转链接使用统一的浅蓝色 `#4fc3f7`，在深色代码背景下清晰可见
- 标题行如有自引用需求，使用显式 `<a id="slug"></a>` 放在标题前，而非包裹标题文字
- 返回链接默认内联放置（不加 `float:right`），仅当需要视觉分离时才使用 `float:right`
- 目录树里的目录名随项目演进可能变化（如 `cservice_src` → `cservice-src`），生成时参照实际仓库结构

## 示例

**输入（文字）：**
```
帮我把这段内容生成一篇博客：TypeScriptToLua 是一个将 TS 转 Lua 的工具...
```

**输出文件 `content/posts/tstl-to-lua-about.md`：**
```markdown
---
title: TSTL 转 Lua 工具介绍
date: 2026-06-03
slug: tstl-to-lua-about
tags: [TSTL, TypeScript, Lua]
description: TypeScriptToLua 将 TypeScript 转译为 Lua 的工具介绍。
---

TypeScriptToLua 是一个将 TS 转 Lua 的工具...
```

**输入（文件，带 front matter）：**
```
把 ts2lua文档记录.md 变成博客文章
```
原文 front matter: `title: ts2lua文档记录`, `date: 2025-07-16`

**输出文件 `content/posts/tstl-docs.md`：**
```markdown
---
title: TSTL 文档记录
date: 2025-07-16
slug: tstl-docs
---

<文件原文内容，保留原有 front matter 中的其他字段如 tags 等>
```

**输入（文件，无 front matter）：**
```
把 notes.txt 变成博客文章
```
文件名中无日期信息。

**输出文件 `content/posts/notes.md`：**
```markdown
---
title: notes
date: 2026-07-04
slug: notes
---

<文件原文内容，日期使用当天日期>
```

**输入（带公式 + 图表 + 封面）：**
```markdown
把这段生成博客，里面有状态机图和贝叶斯公式
```

**输出文件 `content/posts/bayes-intro.md`：**
```markdown
---
title: 贝叶斯公式入门
date: 2026-07-04
slug: bayes-intro
tags: [概率论, 数学]
cover: static/images/bayes.png
---

## 状态机

\`\`\`mermaid
graph LR
A[先验] --> B[观测] --> C[后验]
\`\`\`

## 公式

$$P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}$$

行内写法 \(P(A)\) 表示 A 的概率。
```
