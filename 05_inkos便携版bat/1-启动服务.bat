@echo off
:: 强制使用 UTF-8 编码，解决中文乱码问题
chcp 65001 >nul
title Inkos - 启动服务

:: 1. 定义目录变量，保持逻辑清晰
set "NODE_DIR=%~dp0NodeEnv"
set "CORE_DIR=%~dp0AppCore"
set "USER_DIR=%~dp0UserData"

:: 2. 如果什么都没有，自动创建核心目录和用户数据目录 (去掉了导致报错的括号)
if not exist "%CORE_DIR%" (
    echo [初始化] 正在创建应用核心目录 AppCore...
    mkdir "%CORE_DIR%"
)
if not exist "%USER_DIR%" (
    echo [初始化] 正在创建用户数据目录 UserData...
    mkdir "%USER_DIR%"
)

:: 3. 临时注入便携版 Node 环境及局部的 bin 命令（退出cmd即失效，零污染）
set PATH=%NODE_DIR%;%CORE_DIR%\node_modules\.bin;%PATH%

:: 4. 智能检测：如果 AppCore 里没有安装 inkos，则自动去调起更新脚本拉取
if not exist "%CORE_DIR%\node_modules\@actalk\inkos" (
    echo [提示] 未检测到 Inkos 核心文件，正在首次拉取...
    call "%~dp02-更新核心.bat"
)

:: 5. 进入用户专属的工作区目录，确保配置文件生成在这里
cd /d "%USER_DIR%"

:: 6. 直接启动
inkos

pause