@echo off
REM 灯光参数转辐射瓦特计算器 - 打包脚本
REM Build script for Lighting Parameters to Radiant Watts Calculator

echo ========================================
echo 灯光参数转辐射瓦特计算器 - 打包脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

echo [1/5] 检查Python版本...
python --version

echo.
echo [2/5] 安装PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [错误] PyInstaller安装失败
    pause
    exit /b 1
)

echo.
echo [3/5] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo [4/5] 开始打包EXE文件...
echo 这可能需要几分钟时间，请耐心等待...

pyinstaller ^
    --name="灯光参数转辐射瓦特计算器" ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data="README.md;." ^
    calculator_gui.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo [5/5] 清理临时文件...
if exist build rmdir /s /q build
if exist *.spec del /q *.spec

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo EXE文件位置: dist\灯光参数转辐射瓦特计算器.exe
echo.
echo 你可以将整个 dist 文件夹分享给同事使用
echo.

pause
