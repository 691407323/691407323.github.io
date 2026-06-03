---
name: new-post
description: 将用户输入的文字或文件内容生成为符合博客格式的 Markdown 文章。直接描述需求或提供文件路径即可，例如"帮我把这段文字生成一篇博客"或"把 xxx.md 变成博客文章"。
---

## 触发方式

直接对 Claude 说"生成一篇博客文章"、"把这段内容写成博客"或直接粘贴文件路径，无需使用任何斜杠命令。

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
   - 若原文已有 front matter（`---` 包裹的元数据），保留原文中的 `title`/`date`/`slug` 以外的字段（如 tags、description、categories）
   - 覆盖或补充 `title`、`date`、`slug` 三个字段
   - 若原文无 front matter，按标准格式生成
8. **保存文件**：写入 `content/posts/<slug>.md`
9. **通知用户**：报告生成的文件路径、标题和日期来源

> **提示**：`build.py` 会自动扫描 `content/posts/` 目录下的所有 `.md` 文件，新文章无需手动注册，构建时自动包含。

## 多文件处理

- 若用户一次提供多个文件路径，**依次生成多篇独立文章**
- 每篇使用各自的文件名和内容
- 逐个报告结果，不合并为单篇

## 格式要求

- Front matter 必须包含 `title`、`date`、`slug`
- 保留原文 front matter 中的自定义字段（tags、description、categories 等）
- 正文保持原文结构和格式，不做内容删减
- 支持代码块、表格、引用等 Markdown 语法

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 文件路径不存在 | 提示"文件不存在：xxx"，请用户检查路径 |
| 文件读取失败 | 提示"无法读取文件：xxx"，列出可能原因 |
| 输入内容为空 | 提示"内容为空，请提供文字内容或文件路径" |
| slug 冲突 | 自动追加编号（slug-2、slug-3...） |
| 无写入权限 | 提示"无法写入 content/posts/ 目录，请检查权限" |

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
date: 2026-06-03
slug: notes
---

<文件原文内容，日期使用当天日期>
```
