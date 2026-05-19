# Obsidian 便携版制作说明

## 概述

[Obsidian](https://obsidian.md/) 是一款优秀的 Markdown 笔记软件，但官方只提供安装版（NSIS 安装包）。本教程教你如何将 Obsidian 安装包"拆解"为绿色便携版，配合 [`启动Obsidian.bat`](启动Obsidian.bat) 脚本实现：

- **数据完全隔离**：所有配置、插件、缓存全部存储在程序所在目录，不写入系统 `%APPDATA%` 等位置
- **U盘即插即用**：整个文件夹拷贝到任何 Windows 电脑上均可直接运行，数据随身携带
- **不留痕迹**：不会在宿主电脑上留下任何个人数据

---

## 准备工作

| 工具 | 用途 |
|------|------|
| [7-Zip](https://www.7-zip.org/) 或 [Bandizip](https://www.bandizip.com/) | 解压 NSIS 安装包 和 `app-64.7z` |
| 本仓库的 [`启动Obsidian.bat`](启动Obsidian.bat) | 启动脚本 |

---

## 操作步骤

### 第一步：下载 Obsidian 安装包

前往 Obsidian 官方下载页面：

> **https://obsidian.md/download**

下载 **Windows** 版本的安装程序（文件名类似 `Obsidian-1.x.x.exe`）。

### 第二步：解压 NSIS 安装包

Obsidian 的 `.exe` 安装程序本质上是一个 **NSIS（Nullsoft Scriptable Install System）** 自解压包。我们需要用解压工具将其"拆开"，而不是直接双击运行安装。

1. 右键点击 `Obsidian-1.x.x.exe`，选择 **7-Zip → 提取到 "Obsidian-1.x.x\"**（或其他解压工具类似操作）
2. 解压后你会看到如下目录结构：

```
Obsidian-1.x.x\
├── $PLUGINSDIR\
│   └── app-64.7z        ← 真正的 Obsidian 程序压缩包
├── $R0\
├── $R1\
├── Uninstall Obsidian.exe
├── Obsidian.exe          ← 这其实只是 NSIS 的安装引导程序，不是主程序
└── ...
```

> **关键点**：这里解压出来的 `Obsidian.exe` 只是安装引导程序，**不是** Obsidian 主程序。真正的主程序还在 `$PLUGINSDIR\app-64.7z` 里面。

### 第三步：二次解压 `app-64.7z`

1. 进入 `$PLUGINSDIR` 目录
2. 右键点击 `app-64.7z`，选择 **7-Zip → 提取到 "app-64\"**
3. 解压后你会看到 Obsidian 的真正程序文件：

```
app-64\
├── Obsidian.exe          ← ★ 这才是真正的主程序
├── resources\
├── locales\
├── ...
```

### 第四步：组装便携版目录

将第三步解压出的 `app-64\` 文件夹内的**所有文件**复制到一个新目录（例如 `Obsidian-Portable\`），然后将 [`启动Obsidian.bat`](启动Obsidian.bat) 也放入该目录。

最终目录结构如下：

```
Obsidian-Portable\           ← 你的便携版根目录
├── 启动Obsidian.bat          ← 双击此文件启动
├── Obsidian.exe             ← 主程序（来自 app-64.7z）
├── resources\               ← Obsidian 资源文件
├── locales\                 ← 语言包
├── ...
│
│   （以下目录首次运行后自动生成）
├── UserData\                ← 所有用户数据存这里
│   ├── Roaming\
│   │   └── obsidian\        ← Obsidian 配置/插件/主题
│   └── Local\
└── MyNovels\                ← 默认笔记仓库（Vault）
```

---

## BAT 脚本详解

[`启动Obsidian.bat`](启动Obsidian.bat) 共分4步，每一步都有明确的用途：

### 步骤1：强制切换到脚本所在目录

```batch
cd /d "%~dp0"
```

- `%~dp0` = 脚本自身的盘符+路径，例如 `D:\Obsidian-Portable\`
- `cd /d` = 同时切换盘符和目录
- **意义**：无论你从哪里调用这个 bat（快捷方式、命令行等），工作目录始终锁定在便携版根目录

### 步骤2：自动创建目录架构（防呆设计）

```batch
if not exist "UserData" mkdir "UserData"
if not exist "UserData\Roaming" mkdir "UserData\Roaming"
if not exist "UserData\Local" mkdir "UserData\Local"
if not exist "MyNovels" mkdir "MyNovels"
```

- 首次运行时自动创建所需的目录结构
- `if not exist` 确保已有目录不会被覆盖
- `MyNovels` 是预设的笔记仓库（Vault）目录

### 步骤3：重定向系统环境变量（数据隔离核心）

```batch
set "USERPROFILE=%CD%\UserData"
set "APPDATA=%CD%\UserData\Roaming"
set "LOCALAPPDATA=%CD%\UserData\Local"
```

- 将 Windows 标准用户数据路径全部"劫持"到本地目录
- `%CD%` = 当前目录（已在步骤1中锁定为便携版根目录）
- **效果**：Obsidian 及其子进程（如插件安装器）所有读写操作都落在便携版目录内，**不会触碰系统盘任何用户目录**

### 步骤4：启动 Obsidian 并指定数据目录

```batch
start "" "Obsidian.exe" --user-data-dir="%CD%\UserData\Roaming\obsidian" "%CD%\MyNovels"
```

- `start ""` = 打开新窗口运行程序（bat 自身可以立即退出）
- `--user-data-dir=...` = **强制指定** Obsidian 的底层数据目录（配置、插件、缓存等），双重保险确保数据不会写到系统默认位置
- `"%CD%\MyNovels"` = 启动时自动打开 `MyNovels` 作为 Obsidian Vault（笔记仓库）

---

## 运行方式

1. 确保 `启动Obsidian.bat` 和 `Obsidian.exe` 在同一目录下
2. 双击 `启动Obsidian.bat` 即可运行
3. 首次启动后，`UserData\` 和 `MyNovels\` 目录会自动生成

> **提示**：你可以右键 `启动Obsidian.bat` → 发送到桌面快捷方式，方便日常使用。

---

## 常见问题

**Q：为什么不能直接双击 `Obsidian.exe`？**

A：直接双击 `Obsidian.exe` 会把配置和数据写入系统 `%APPDATA%\obsidian\` 目录，失去了便携版的意义。必须通过 `启动Obsidian.bat` 启动，才能确保数据隔离。

**Q：更新 Obsidian 版本怎么办？**

A：重新下载最新版安装包，按上述步骤解压 `app-64.7z`，将解压出的文件覆盖到便携版目录即可。你的 `UserData\` 和 `MyNovels\` 数据不会受影响。

**Q：可以更改 Vault 目录名吗？**

A：可以。修改 [`启动Obsidian.bat`](启动Obsidian.bat) 第9行的 `MyNovels` 和第17行末尾的 `MyNovels` 为你想要的目录名即可。
