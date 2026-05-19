@echo off
title 禁用 Windows 自动更新 (终极纯净版 V2)
color 0A

:: 1. 更兼容的自动提权检查 (使用 net session 替代弃用的 cacls)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [提示] 正在请求管理员权限...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B
)
if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
pushd "%CD%"
CD /D "%~dp0"

echo ==========================================
echo       Windows 更新彻底禁用脚本 V2
echo ==========================================
echo.

echo [1/4] 写入组策略/注册表级拦截规则...
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v ExcludeWUDriversInQualityUpdate /t REG_DWORD /d 1 /f >nul 2>&1

echo [2/4] 强制停止正在运行的更新进程...
net stop wuauserv >nul 2>&1
net stop UsoSvc >nul 2>&1
net stop WaaSMedicSvc >nul 2>&1

echo [3/4] 底层锁定核心服务及“更新医疗服务”...
:: 使用注册表直接修改服务启动类型为禁用 (数值 4)，绕过 sc config 的 TrustedInstaller 权限拦截
reg add "HKLM\SYSTEM\CurrentControlSet\Services\wuauserv" /v Start /t REG_DWORD /d 4 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\UsoSvc" /v Start /t REG_DWORD /d 4 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc" /v Start /t REG_DWORD /d 4 /f >nul 2>&1

echo [4/4] 抹除 Windows 更新后台唤醒计划任务...
schtasks /Change /TN "\Microsoft\Windows\WindowsUpdate\Scheduled Start" /Disable >nul 2>&1

echo.
echo ==========================================
echo 部署完成！更新通道、医疗服务及计划任务均已被底层物理切断。
echo 请按任意键退出，建议重启系统使所有注册表项彻底接管系统行为。
echo ==========================================
pause >nul