---
title: Skynet-cmake 跨平台使用
date: 2026-06-03
slug: skynet-cmake-usage
tags: [Skynet, CMake, TSTL]
---

## 简介

基于 [hanxi/skynet-cmake](https://github.com/hanxi/skynet-cmake) 项目，新增 skynet 框架的使用，并做了以下调整和 bug 修复。同时引入 TSTL（TypeScriptToLua）来替代传统 Lua 脚本编写方式。

## 项目层级

项目目录结构调整如下：

<pre id="folder-tree">
core/
├── skynet/
├── posix/
└── pthread-win32/
cservice-src/
luaclib-src/
└── <a href="#1-lua-winhelp-windows" style="color:#4fc3f7;">[→ lua-winhelp]</a>
ts/
├── src/
├── tools/
└── interface/
build/
buildWin/
CMakeLists.txt
</pre>

## Skynet-cmake-win Bug 记录

### 1. 修复 `unistd.h` 启动 log 调用

时间转换函数在 Windows 和 Linux 上表现不一致：

- **Windows**: `_localtime64(struct tm, time_t)`
- **Linux**: `localtime_r(time_t, struct tm)`

调用方式需要区分平台，避免参数顺序导致的编译或运行时错误。

### 2. 修复 Windows 下 socket 断开问题

Windows 下 `read` 函数在 socket 非阻塞模式下遇到 `WSAEWOULDBLOCK` 时会被当作异常断开。修复方案：

```c
int wsaerr = WSAGetLastError();
if (wsaerr == WSAEWOULDBLOCK) {
    errno = EWOULDBLOCK;
}
```

将 `WSAEWOULDBLOCK` 映射为 `EWOULDBLOCK`，使上层逻辑无需区分平台即可正确处理非阻塞读未就绪的情况。

## 附录

### 1. lua-winhelp — Windows 控制台输入模块 <a href="#folder-tree" style="color:#4fc3f7;">[↩]</a>

在 Windows 平台下，skynet 的控制台输入处理与 Linux 存在差异。`lua-winhelp.c` 提供了一套 Windows 原生的 stdin 解决方案，通过独立线程异步读取控制台输入，避免阻塞 skynet 主线程。

#### 核心设计

- 使用 `atomic_bool` 标记输入是否就绪，实现线程间安全通信
- 后台线程通过 `fgets` 阻塞读取 stdin，就绪后通知主线程
- 提供三个 Lua 接口：初始化线程、获取输入结果、关闭线程

```c
static DWORD WINAPI readInput(LPVOID lpParam) {
    while(!input_end){
        fgets(input, sizeof(input), stdin);  // 阻塞读取输入
        input_ready = TRUE;                  // 标记输入已准备好
    }
    return 0;
}
```

#### Lua 接口

| 函数 | 说明 |
|------|------|
| `initWinThread()` | 启动后台输入线程 |
| `getWinThreadResultFlag()` | 获取用户输入字符串，无输入返回 nil |
| `closeWinThread()` | 关闭线程并等待退出 |

#### 完整源码

```c
//
// Created by Vermouth on 2024/1/24.
//

#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <stdatomic.h>

static atomic_bool input_ready = ATOMIC_VAR_INIT(FALSE);  // 原子变量，表示输入是否准备好
static BOOL input_end = FALSE;
static char input[256];                                   // 存储用户输入的全局变量
static HANDLE input_thread;

static DWORD WINAPI readInput(LPVOID lpParam) {
    while(!input_end){
        fgets(input, sizeof(input), stdin);  // 阻塞读取输入
        input_ready = TRUE;                  // 标记输入已准备好
    }
    return 0;
}

static int linitWinThread(lua_State *L){
    input_thread = CreateThread(
            NULL,          // 默认安全属性
            0,             // 默认堆栈大小
            readInput,     // 线程函数
            NULL,          // 参数
            0,             // 立即运行线程
            NULL           // 不需要线程ID
    );
    input_ready = FALSE;
    if (input_thread == NULL) {
        fprintf(stderr, "无法创建线程\n");
        return 1;
    }
    return 1;
}

static int lgetWinThreadResultFlag(lua_State *L){
    if(input_ready){
        lua_pushstring(L, input);
    }else{
        lua_pushnil(L);
    }
    input_ready = FALSE;
    return 1;
}

static int lcloseWinThread(lua_State *L){
    input_end = TRUE;
    WaitForSingleObject(input_thread, INFINITE);
    CloseHandle(input_thread);
}

static const luaL_Reg l[] = {
        {"initWinThread",linitWinThread},
        {"getWinThreadResultFlag",lgetWinThreadResultFlag},
        {"closeWinThread",lcloseWinThread},
        {NULL, NULL},
};

int luaopen_winhelp(lua_State *L) {
    luaL_newlib(L, l);
    return 1;
}
```
