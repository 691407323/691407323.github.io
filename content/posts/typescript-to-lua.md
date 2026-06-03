---
title: TypeScript to Lua
date: 2025-07-16
slug: tstl-to-lua-about
---

TypeScriptToLua（简称 TSTL）是一个将 TypeScript 代码转译为 Lua 代码的工具。实际使用过程中会遇到很多需要手动处理或记住的规则，本文记录转换过程中的关键注意事项。

## 类方法 vs 对象方法

Lua 中使用 `:` 调用时，会自动传入 `self` 作为第一个参数；使用 `.` 调用时则需要显式传参。

TS 中的约定与 Lua 的对应关系：

| TS 类型 | Lua 调用方式 |
|---------|--------------|
| 类方法（`static`） | `模块.xxx()` |
| 对象方法（非 `static`） | `self:xxx()` |

注意 TS 中 `any` 类型转换后也会变成 `::` 调用，因此需要对 Lua 模块文件名定义一些通用类型，例如直接定义类型、`typeof` 继承类型、`as unknown as xxx` 等方式。

## private / public / static

```typescript
// TS 写法
class Foo {
    private static version = "1.0"   // → Lua: local 变量
    public static name = "foo"        // → Lua: 模块级全局变量
    public bar: string                // → Lua: 对象属性

    public static init()              // → Lua: 模块.xxx()
    public update()                   // → Lua: self:xxx()
}
```

对应关系：

| TS 修饰符 | Lua 中的表现 |
|-----------|-------------|
| `private` | Lua 模块中的 `local` |
| `public` | Lua 模块的全局 |
| `static` | 类方法，调用时用 `.` |
| 非 `static` | 对象方法，调用时用 `:` |

## this 参数问题

需要在 TS 文件、类、方法上添加 `@noSelfInFile`、`@noSelf` 注释，或使用 `this: void` 来控制 Lua 中是否保留 `self` 参数。

```typescript
/** @noSelfInFile */   // 文件级别：文件内的类不会被处理 self
/** @noSelf **/        // 类或方法级别：不传递 self
// 或在方法签名中使用
method(this: void): void { }
```

## 初始化与清理

TS 中可提供两个特殊函数，对应 Lua 生命周期：

```typescript
function luaMInit(): void { }
function luaMFinal(): void { }
```

## 数组索引问题

TS 中的数组 `[]` 在转换到 Lua 时索引会自动 **+1**（Lua 索引从 1 开始）。如果不想自动 +1，改用 `{}` 代替 `[]`。

> 控制这个行为的源码开关是 `transformElementAccessArgument`，如需修改可定位到 TSTL 源码。

```typescript
// TS 写法
const arr: number[] = [1, 2, 3]   // → Lua: {2, 3, 4}（索引 +1）
const tbl: LuaHashTable<number> = { [0]: 1, [1]: 2 }  // → Lua: {[0]=1, [1]=2}（不 +1）
```

## 多参数返回

使用 `$multi` 注解函数可返回多个值。使用 `...` 展开多参数时，部分场景需要配合 `any` 返回类型和去掉 `createUnpackCall` 来正确处理。

```typescript
function getPos(): $multi<{ x: number, y: number }> { ... }

// 调用方式
let { x, y } = getPos()     // 解构赋值
let [x, y] = getPos()       // 数组解构
let pos = getPos()          // 整体接收
```

## TSTL 源码改动记录

为解决上述问题，直接修改了 TSTL 源码。主要涉及四个文件：

### function-context.ts

`hasNoSelfAncestor` 默认返回 `true`。

### lua-ast.ts

- 注释了 `LuaLibFeature` 导入
- `createUnpackCall` 改为直接 `return expression`
- 新增 `wrapInTable` 逻辑

### access.ts

数组索引偏移从 `+1` 改为 `+0`，使 TS 数组索引与 Lua 保持一致。

### call.ts

- 新增 `static` 方法判断逻辑
- `wrapResultInTable` 强制为 `false`

### function.ts

`static` 方法不绑定 `self` 参数。

## 小结

本文记录 TypeScriptToLua 转换中最常遇到的核心规则，包括方法调用方式、类型可见性、this 处理、数组索引偏移、多返回值等，以及对应的源码修改。掌握这些规则能大幅减少转译后的调试成本。
