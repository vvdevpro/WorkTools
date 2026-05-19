# Inkos 便携版使用说明

## 什么是 Inkos

[Inkos](https://github.com/Narcooo/inkos) 是一款基于 Node.js 的 AI 自动写小说工具，通过 npm 包 `@actalk/inkos` 分发。本便携版方案将 Node.js 运行时、程序核心、用户数据三者分离并全部存放在同一目录下，实现：

- **零系统污染**：不修改系统 `PATH`，不写入 `%APPDATA%`，所有依赖和配置皆在便携版目录内
- **开箱即用**：首次运行自动拉取最新版 Inkos，无需手动 `npm install`
- **数据随身携带**：整个文件夹拷贝到任何 Windows 电脑上即可运行，小说进度和配置不会丢失

---

## 准备工作

| 工具/文件 | 用途 |
|-----------|------|
| [Node.js](https://nodejs.org/zh-cn/download) | 提供 `node.exe` 和 `npm.cmd` 运行环境 |
| [`1-启动服务.bat`](1-启动服务.bat) | 启动 Inkos 的主脚本 |
| [`2-更新核心.bat`](2-更新核心.bat) | 拉取/更新 Inkos 最新版本 |

---

## 操作步骤

### 第一步：下载 Node.js

前往 Node.js 官方下载页面：

> **https://nodejs.org/zh-cn/download**

选择 **Windows 预构建二进制文件**（Prebuilt Binaries）中的 `.zip` 版本（**不是 `.msi` 安装包**）。

例如下载 `node-vXX.XX.X-win-x64.zip`。

### 第二步：解压 Node.js 到 `NodeEnv`

1. 将下载的 `node-vXX.XX.X-win-x64.zip` 解压
2. 解压后你会看到 `node.exe`、`npm.cmd`、`npx.cmd` 等文件，它们通常在一个名为 `node-vXX.XX.X-win-x64` 的文件夹内
3. 将该文件夹内的**所有文件**复制到便携版目录的 `NodeEnv\` 中

**正确结构示例**：

```
NodeEnv\
├── node.exe          ← Node.js 主程序
├── npm.cmd           ← npm 包管理器
├── npx.cmd           ← npx 包执行器
├── node_modules\     ← npm 自带的（如果有）
└── ...
```

### 第三步：启动 Inkos

双击 [`1-启动服务.bat`](1-启动服务.bat) 即可。

首次运行时脚本会自动完成以下初始化工作，后续运行则直接启动：

| 阶段 | 自动操作 |
|------|----------|
| 首次启动 | 创建 `AppCore\` 目录 → 调用 [`2-更新核心.bat`](2-更新核心.bat) → `npm i @actalk/inkos@latest` 拉取最新版 → 创建 `UserData\` 目录 → 启动 Inkos |
| 后续启动 | 直接启动 Inkos，进入 `UserData\` 工作区 |

---

## 最终目录结构

首次运行后完整目录如下：

```
Inkos-Portable\                     ← 你的便携版根目录
├── 1-启动服务.bat                   ← 双击启动 Inkos
├── 2-更新核心.bat                   ← 手动更新 Inkos 核心（也可被 1 自动调用）
│
├── NodeEnv\                         ← Node.js 运行环境（需手动放入）
│   ├── node.exe
│   ├── npm.cmd
│   └── ...
│
├── AppCore\                         ← 自动创建，存放 Inkos 程序核心
│   ├── node_modules\
│   │   └── @actalk\
│   │       └── inkos\              ← Inkos 主程序
│   ├── package.json
│   └── package-lock.json
│
└── UserData\                        ← 自动创建，存放用户数据
    └── ...                          ← 聊天记录、配置文件等
```

---

## BAT 脚本详解

### [`1-启动服务.bat`](1-启动服务.bat) — 主启动脚本

```batch
chcp 65001 >nul
title Inkos - 启动服务
```

- `chcp 65001` 强制切换终端编码为 UTF-8，避免中文输出乱码

```batch
set "NODE_DIR=%~dp0NodeEnv"
set "CORE_DIR=%~dp0AppCore"
set "USER_DIR=%~dp0UserData"
```

- 定义三个核心目录变量，均相对于脚本所在目录

```batch
if not exist "%CORE_DIR%" (
    echo [初始化] 正在创建应用核心目录 AppCore...
    mkdir "%CORE_DIR%"
)
if not exist "%USER_DIR%" (
    echo [初始化] 正在创建用户数据目录 UserData...
    mkdir "%USER_DIR%"
)
```

- **防呆设计**：首次运行时自动创建 `AppCore\` 和 `UserData\` 目录

```batch
set PATH=%NODE_DIR%;%CORE_DIR%\node_modules\.bin;%PATH%
```

- **临时注入环境变量**：将 `NodeEnv\`（Node.js 运行时）和 `.bin`（npm 全局命令）加入本次 cmd 会话的 `PATH`，退出即失效，零污染

```batch
if not exist "%CORE_DIR%\node_modules\@actalk\inkos" (
    echo [提示] 未检测到 Inkos 核心文件，正在首次拉取...
    call "%~dp02-更新核心.bat"
)
```

- **智能检测**：如果 `AppCore\` 中没有 Inkos，自动调用 [`2-更新核心.bat`](2-更新核心.bat) 拉取最新版本

```batch
cd /d "%USER_DIR%"
inkos
```

- 切换到 `UserData\` 作为工作目录，确保用户配置和数据全部生成在此
- 执行 `inkos` 命令启动服务

```batch
pause
```

- 窗口保持打开，方便查看运行日志

### [`2-更新核心.bat`](2-更新核心.bat) — 核心更新脚本

```batch
set "NODE_DIR=%~dp0NodeEnv"
set "CORE_DIR=%~dp0AppCore"

if not exist "%CORE_DIR%" mkdir "%CORE_DIR%"

set PATH=%NODE_DIR%;%PATH%
cd /d "%CORE_DIR%"

call npm i @actalk/inkos@latest
```

- 进入 `AppCore\` 目录，从 npm registry 拉取 `@actalk/inkos` 最新版本
- `@latest` 确保每次更新都获取最新版
- 更新不会触碰 `UserData\`，用户数据完全安全

---

## 运行方式

1. 确保 `NodeEnv\` 下包含 `node.exe` 和 `npm.cmd`
2. 双击 [`1-启动服务.bat`](1-启动服务.bat)
3. 首次启动需联网，npm 会自动下载 Inkos，请耐心等待
4. 后续启动无需联网，直接进入 Inkos

---

## 常见问题

**Q：为什么提示 `"inkos" 不是内部或外部命令`？**

A：可能原因：
1. `NodeEnv\` 目录下没有 `node.exe`，请检查是否已正确解压 Node.js zip 包
2. 首次启动时未联网，无法从 npm 拉取 Inkos

**Q：如何更新 Inkos 到最新版？**

A：双击 [`2-更新核心.bat`](2-更新核心.bat) 即可，它会重新执行 `npm i @actalk/inkos@latest`，你的 `UserData\` 数据不会受影响。

**Q：可以更换 Node.js 版本吗？**

A：可以。去 [Node.js 下载页](https://nodejs.org/zh-cn/download) 下载其他版本的 zip 包，覆盖 `NodeEnv\` 目录即可。

**Q：Installing Inkos to a different directory than AppCore?**

A：No. All paths are hardcoded relative to the script location. If you want to change this, edit the `CORE_DIR` variable in both `.bat` files.
