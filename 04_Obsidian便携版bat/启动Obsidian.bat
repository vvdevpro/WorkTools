@echo off
:: 1. 强制切换到当前工作目录
cd /d "%~dp0"

:: 2. 极致防呆：自动创建所有基础目录架构
if not exist "UserData" mkdir "UserData"
if not exist "UserData\Roaming" mkdir "UserData\Roaming"
if not exist "UserData\Local" mkdir "UserData\Local"
if not exist "MyNovels" mkdir "MyNovels"

:: 3. 全面拦截系统环境变量，确保数据绝对隔离、不留痕
set "USERPROFILE=%CD%\UserData"
set "APPDATA=%CD%\UserData\Roaming"
set "LOCALAPPDATA=%CD%\UserData\Local"

:: 4. 启动程序，强制锁定底层数据目录，并直接挂载小说仓库
start "" "Obsidian.exe" --user-data-dir="%CD%\UserData\Roaming\obsidian" "%CD%\MyNovels"