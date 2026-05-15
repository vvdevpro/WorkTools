@echo off
title 恢复 Windows 自动更新
color 0B

:: 1. 自动提权检查
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
echo       Windows 更新恢复脚本
echo ==========================================
echo.

echo [1/4] 清除组策略/注册表级拦截规则...
:: 准确删除之前添加的禁用键值，不误伤其他策略
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /f >nul 2>&1
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v ExcludeWUDriversInQualityUpdate /f >nul 2>&1

echo [2/4] 底层解锁核心服务及“更新医疗服务”...
:: wuauserv (Windows Update) 默认通常为手动(3)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\wuauserv" /v Start /t REG_DWORD /d 3 /f >nul 2>&1
:: UsoSvc (更新编排服务) 默认通常为自动-延迟启动(2)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\UsoSvc" /v Start /t REG_DWORD /d 2 /f >nul 2>&1
:: WaaSMedicSvc (更新医疗服务) 默认通常为手动(3)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\WaaSMedicSvc" /v Start /t REG_DWORD /d 3 /f >nul 2>&1

echo [3/4] 尝试唤醒核心更新服务...
net start wuauserv >nul 2>&1
net start UsoSvc >nul 2>&1

echo [4/4] 恢复 Windows 更新后台唤醒计划任务...
schtasks /Change /TN "\Microsoft\Windows\WindowsUpdate\Scheduled Start" /Enable >nul 2>&1

echo.
echo ==========================================
echo 恢复完成！更新通道已被重新打通。
echo 请按任意键退出。建议重启系统后，进入“设置 - Windows 更新”手动检查一次。
echo ==========================================
pause >nul