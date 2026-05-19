@echo off
:: 强制使用 UTF-8 编码
chcp 65001 >nul
title Inkos - 更新核心
echo 正在准备检查并更新程序...

:: 定义目录变量
set "NODE_DIR=%~dp0NodeEnv"
set "CORE_DIR=%~dp0AppCore"

:: 确保核心目录存在，防止误删后更新报错
if not exist "%CORE_DIR%" (
    mkdir "%CORE_DIR%"
)

:: 注入便携版 Node 环境
set PATH=%NODE_DIR%;%PATH%

:: 进入核心存放目录
cd /d "%CORE_DIR%"

:: 执行安装
echo 正在拉取最新版本，请稍候...
call npm i @actalk/inkos@latest

echo.
echo ==============================================
echo 更新完成！你的 UserData 工作区数据未受任何影响。
echo ==============================================
pause