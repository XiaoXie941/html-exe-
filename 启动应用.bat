@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   网页打包工具 - 启动脚本
echo ========================================
echo.

:: 启动应用程序
python main.py

:: 如果程序正常退出
if errorlevel 0 (
    echo.
    echo [信息] 应用程序已正常退出
) else (
    echo.
    echo [警告] 应用程序异常退出，错误代码: %errorlevel%
)

pause