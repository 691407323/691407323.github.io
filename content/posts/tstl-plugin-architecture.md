---
title: TSTL 插件架构
date: 2025-03-16
slug: tstl-plugin-architecture
tags: [TSTL, TypeScript, Lua, 架构]
---

本文系统梳理一套基于 TypeScriptToLua (TSTL) 的自定义插件的完整实现，涵盖从增量编译到 AST 转换、代码生成的全流程。

## 整体架构

这套插件的核心目标：

- 将 TypeScript 编译为接近手写 Lua 5.3/5.4 的代码
- 移除模块系统（不生成 require/exports），类作为全局模块
- 简化类模型（用 `____M` 变量代替复杂 `__TS__Class()` 包装）
- 内联特殊方法（luaMInit / luaMFinal / init 静态方法直接展开）
- 支持增量编译 + 内嵌原生 Lua 代码

插件执行顺序：`beforeTransform` → `visitors` → `beforeEmit` → `afterPrint` → `printer` → `afterEmit`

## beforeTransform.ts — 增量编译

实现增量编译 + 自动复制非 TS 资源文件到输出目录。

通过 `file-timestamps.txt` 记录每个源文件的 ctime+mtime 组合，判断文件是否有变化。未变化的文件从 `program.getSourceFiles()` 中移除，TSTL 直接跳过。同时递归复制非 `.ts` 资源文件到输出目录，同样带时间戳校验。

```typescript
class Plugin implements tstl.Plugin {
    private unchangedFiles: ts.SourceFile[] = [];
    private timestamps: Record<string, string> = {};
    private timestampFile = path.resolve("./", "file-timestamps.txt");
}
```

关键逻辑：

1. 加载历史时间戳
2. 检查每个源文件的 `ctime+mtime` 组合字符串，判断是否有变化
3. 未变化的文件从 `program.getSourceFiles()` 中 splice 移除
4. 递归复制非 `.ts` 资源文件到输出目录
5. 将更新后的时间戳写回文件

## visitors.ts — 核心 AST 转换（最重要）

注册了多个自定义 Visitor，重写默认的 TS→Lua 转换逻辑。

### 注册入口

```typescript
const plugin: tstl.Plugin = {
    visitors: {
        [ts.SyntaxKind.ImportDeclaration]:  (node, context) => undefined,     // 移除 import
        [ts.SyntaxKind.ExportDeclaration]:  (node, context) => undefined,     // 移除 export
        [ts.SyntaxKind.ClassDeclaration]:   visitClassDeclaration2,            // 核心：类重写
        [ts.SyntaxKind.ThisKeyword]:        visitThis,                         // this 指针处理
        [ts.SyntaxKind.SourceFile]:         sourceFile,                        // 重置计数器
        [ts.SyntaxKind.CallExpression]:     callExpression,                    // 方法调用
        [ts.SyntaxKind.PropertyAccessExpression]: propertyAccessExpression,    // 属性访问
        [ts.SyntaxKind.Identifier]:         identifier,                        // 特殊标识符
        [ts.SyntaxKind.FunctionDeclaration]: functionDeclaration,              // 函数特殊处理
    },
};
```

### 类声明核心转换（visitClassDeclaration2）

用 `____M`（或其变体）代替 `__TS__Class()`，简化类模型，处理 init / private / static。

核心产出（Lua）：

```lua
local ____M = __TS__Class()          -- 基础类壳
MyClass = ____M                      -- 全局注入
local ____M = MyClass                -- 模块变量声明
-- ...成员绑定...
```

关键概念：

| 概念 | 说明 |
|------|------|
| `____M` | 类模块变量，代替默认 `__TS__Class()` 的类引用 |
| `____M_tempN` | 嵌套类时的模块变量，N 为嵌套层级 |
| `____ThisBind_temp` | 静态方法中访问 private 成员时的 this 代理变量 |
| `____LocalFuncBind_temp` | private 方法绑定的表对象 |
| `self` | 实例方法中的 this，对应 Lua 的 self |

### this 关键字处理（visitThis）

转换规则：

- 实例方法中 `this` → `self`
- 静态方法中 `this` → `____M`（或嵌套时的 `____M_tempN`）
- 静态方法中访问 private 成员 → `____ThisBind_temp`

### 方法调用处理（callExpression）

核心区分逻辑：

1. `super.xxx()` → 原型方法调用（`super.____constructor(...)` 等）
2. `private static` 方法 → 直接调用函数名：`methodName(args)`
3. `public static` 方法 → 带模块名调用
4. 普通实例方法 → 走默认转换

### 属性访问处理（propertyAccessExpression）

- `private static` 属性/方法访问 → 直接用属性名（不加模块前缀）
- 其他情况走默认转换

### 特殊标识符（identifier）

核心：`__FUNC__` 魔术常量

```typescript
if (node.text === "__FUNC__") {
    // 自动替换为当前函数名（"类名.方法名" 格式）
    functionName = `${className}.${methodName}`;
}
```

### 函数声明处理（functionDeclaration）

对名为 `luaMInit` 的顶级函数，直接展开为语句块（不生成函数定义）。其余函数走默认转换。

## beforeEmit.ts — 生成前深度处理

在 Lua 文件写入磁盘前做最后的字符串和 AST 处理。

### 特殊函数替换

| TS 宏 | 替换结果 |
|-------|---------|
| `TSRequire(x)` | `require('x')` |
| `StrRequire(x)` | `require(x)` |
| `LuaCode("...")` | 直接嵌入原始 Lua 字符串 |
| `LuaMultiReturnFunc(...)` | 展开内部内容 |
| `Local(xyz)` | `local xyz = xyz` |

### AST 裁剪

用 `luaparse` 解析 Lua AST，定位 `luaMInitFunc = function(...)` 赋值语句，只保留函数体内部内容，剥离外层变量赋值包裹。

### 类模块追加 return

通过匹配 `Xxx.name = "..."` 提取类名，文件末尾追加 `return ____M`。

```typescript
let match = emitFile.code.match(/(\w+)\.name\s*=\s*"/);
if (match) {
    emitFile.code = emitFile.code + '\nreturn ____M\n';
}
```

## afterPrint.ts — 打印后文本处理

对已格式化的 Lua 代码做字符串层面的后处理。

- 移除 `____exports` 相关行
- 移除 `____ThisBind_temp.` 前缀
- 移除 `____LocalFuncBind_temp.` 前缀

## printer.ts — 自定义 Lua 打印机

继承 `LuaPrinter`，重写 `printFile` 在文件头添加注释。

```typescript
class CustomPrinter extends tstl.LuaPrinter {
    protected printFile(file: tstl.File): SourceNode {
        const originalResult = super.printFile(file);
        return this.createSourceNode(file, [
            `${CUSTOM_COMMENT_HEADER} ${this.luaFile}\n`,
            originalResult
        ]);
    }
}
```

## afterEmit.ts — 生成后回调

在 Lua 代码生成完成后触发，记录输出文件信息，打印 TS 原始文件路径和输出文件路径。

## 模块解析（moduleResolution.ts）

简单的模块重定向示例，将特定模块名映射到不同文件。

```typescript
moduleResolution(moduleIdentifier: string, ...) {
    if (moduleIdentifier === "foo") {
        return "bar";
    }
}
```

## 编译流水线总结

```
┌─────────────────────────────────────────────────────────────────┐
│                        TSTL 编译流水线                           │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1: 元数据准备                                              │
│    → beforeTransform.ts: 增量编译，剔除未修改文件，复制资源文件       │
│                                                                  │
│  Phase 2: AST 转换（Visitors）                                   │
│    → visitors.ts 介入，重写 Class/This/Call/Identifier 等         │
│       核心产出：简化的 Lua AST（使用 ____M, self, local 等）        │
│                                                                  │
│  Phase 3: Lua 代码打印                                            │
│    → printer.ts: 可选自定义打印（注释头）                          │
│    → 默认 TSTL LuaPrinter 输出 Lua 字符串                          │
│                                                                  │
│  Phase 4: 打印后处理                                              │
│    → afterPrint.ts: 字符串替换，清理 ____exports/____ThisBind_temp  │
│                                                                  │
│  Phase 5: 生成前处理                                              │
│    → beforeEmit.ts: TSRequire→require, LuaCode嵌入, AST裁剪,       │
│       Local宏展开, 格式化, 追加 return ____M                       │
│                                                                  │
│  Phase 6: 文件写入磁盘                                            │
│                                                                  │
│  Phase 7: 生成后回调                                              │
│    → afterEmit.ts: 记录日志，打印原始文件和输出文件路径              │
└─────────────────────────────────────────────────────────────────┘
```
