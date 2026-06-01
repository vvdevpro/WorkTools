@echo off
chcp 65001 >nul
echo ========================================
echo   轻量 Todo 工具 - 打包脚本
echo   (PyWebView + HTML/CSS)
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/2] 安装依赖...
pip install -r requirements.txt -q

echo [2/2] 正在打包为 EXE...
pyinstaller --onefile --windowed --name "LightTodo" ^
    --add-data "todo_data.json;." ^
    --hidden-import webview ^
    --hidden-import clr_loader ^
    --clean todo_app.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo   EXE 文件位置: dist\LightTodo.exe
echo ========================================
echo.

copy /y "dist\LightTodo.exe" "LightTodo.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo [完成] 已复制到: todo软件\LightTodo.exe
)

pause