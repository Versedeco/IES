@echo off
chcp 65001 >nul
echo ======================================
echo   IES文件格式验证工具
echo ======================================
echo.

if "%~1"=="" (
    echo 请将IES文件拖放到此批处理文件上
    echo 或在命令行中指定文件路径
    echo.
    pause
    exit /b 1
)

python validate_ies.py "%~1"
