---
title: 在博客中插入图片示例
date: 2026-07-04
slug: image-usage-demo
tags: [教程, 图片]
description: 演示在本项目中如何添加/引用图片，含 cover 封面、WebP 自动优化、缩略图与点击放大。
cover: static/images/sample-desktop.png
---

> 本篇是本项目的「图片使用手册」，把图片从放进仓库到前端展示的完整链路走一遍。
> 涉及模块：M-4 front matter 的 `cover`/`tags` 字段、M-13 图片自动 WebP + 缩略图、M-14 `og:image`。

## 一、图片放在哪里

本项目的图片统一放在 `static/images/` 目录下。构建时 `build.py` 会把整个 `static/` 原样复制到 `_site/static/`，所以图片最终可访问路径为：

```
/static/images/<文件名>
```

对应的项目结构：

```
Blog/
├── content/posts/        # Markdown 文章
├── static/images/        # ← 图片放这里
│   └── sample-desktop.png
├── build.py              # 构建脚本（含 M-13 图片处理）
└── _site/                # 构建产物（部署目录）
    └── static/images/
        ├── sample-desktop.png           # 原图（原样复制）
        ├── sample-desktop.webp           # ← 构建自动生成，主图
        └── sample-desktop_thumb.webp    # ← 构建自动生成，缩略图
```

> ⚠️ **关键决策**：Markdown 里的图片路径**不会被自动改写**（参见 `PLAN.md` M-13）。想用 `.webp` 就手写 `.webp`，想用 `.png` 就保留 `.png`。这避免了"自动替换但链接算不准"的坑。

## 二、正文插入图片（直接用原图）

标准 Markdown 语法，绝对路径引用：

```markdown
![示例图片](/static/images/sample-desktop.png)
```

效果如下（这是原图 `sample-desktop.png`，457KB）：

![示例图片](/static/images/sample-desktop.png)

## 三、用自动生成的 WebP（推荐）

构建时 `build.py` 的 `process_images()` 会为每张 PNG/JPG 自动生成：

| 产物 | 宽度 | 体积 | 用途 |
|------|------|------|------|
| `sample-desktop.png` | 775px | 457KB | 原图，原样复制 |
| `sample-desktop.webp` | 775px | **55KB** | 主图，质量 82，体积 **↓88%** |
| `sample-desktop_thumb.webp` | 480px | **20KB** | 缩略图，列表/卡片场景 |

同样一张图，引用 `.webp` 即可享受 8 倍体积优势：

```markdown
![示例图片 WebP](/static/images/sample-desktop.webp)
```

![示例图片 WebP](/static/images/sample-desktop.webp)

肉眼几乎看不出差别，但读者流量省了近 400KB。

## 四、缩略图 + 点击放大

缩略图 `_thumb.webp` 适合正文预览，链接指向大图，用户点开再加载完整图：

```markdown
[![缩略图](/static/images/sample-desktop_thumb.webp)](/static/images/sample-desktop.webp)
```

效果（点缩略图跳转到主图）：

[![缩略图](/static/images/sample-desktop_thumb.webp)](/static/images/sample-desktop.webp)

## 五、封面图（cover 字段 → og:image）

在 front matter 用 `cover` 指定，构建时会自动拼成 `og:image` 绝对 URL，用于社交平台分享卡片：

```yaml
---
title: 在博客中插入图片示例
cover: static/images/sample-desktop.png
---
```

注意 front matter 里**不加前导斜杠**（写 `static/...`）。构建时 `build.py` 会拼成：

```
https://691407323.github.io/static/images/sample-desktop.png
```

> 👉 在本页面右键「查看网页源代码」，搜 `og:image` 就能看到这行已自动渲染。
> M-14 的设计是**条件输出**：没有 `cover` 的文章不会输出空的 `og:image` 标签。

## 六、完整工作流

1. 把图片放进 `static/images/`（建议英文/数字命名）
2. 运行 `python3 build.py`
3. `process_images()` 自动为每张 PNG/JPG 生成 `.webp` + `_thumb.webp`
4. 在 Markdown 正文里引用产物路径（`.webp` 最省流量）
5. 需要社交分享卡片时，在 front matter 加 `cover:`
6. 提交 `_site/` 到 Pages 仓库即可线上生效

## 七、关键提醒与小坑

- **路径不自动改写**：写文章时直接用最终产物路径，不要等构建去替换
- **增量跳过**：源图没改时下次构建会跳过（看日志 `0 张生成，1 张跳过`），不会重复转
- **Pillow 软依赖**：没安装 Pillow 时构建照常通过，只是跳过图片处理并打印提示，不报错
- **中文文件名**：理论上可用，但会触发 URL 编码，强烈建议英文/数字命名
- **WebP 兼容率 95%+**：本项目决策是只转 WebP 不保留原格式兜底，读者群体浏览器足够新
- **移动端自适应**：CSS 已设置 `.post-body img { max-width:100% }`（见 `static/css/style.css:48`），无需手动控制宽度
- **`cover` 是分享卡片缩略图**，不是文章顶部的 banner；要做文章头图需要自己在正文最上方插一张图
