@echo off
REM EXR转IES转换器 - 打包脚本 v2.0 (with Visualization)
REM Build script for EXR to IES Converter

echo ========================================
echo EXR转IES转换器 - 打包脚本 v2.0
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python
    pause
    exit /b 1
)

echo [1/5] 检查Python版本...
python --version

echo.
echo [2/5] 安装依赖库...
echo 正在安装基础依赖...
pip install pyinstaller numpy pillow
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，但可以继续
)

echo.
echo 正在安装可视化依赖 (matplotlib)...
pip install matplotlib
if errorlevel 1 (
    echo [警告] matplotlib安装失败，可视化功能可能不可用
)

echo.
echo [3/5] 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo [4/5] 开始打包EXE (包含可视化功能)...
echo 这可能需要几分钟...

pyinstaller --name=EXR_to_IES_Converter --onefile --windowed --icon=NONE --hidden-import=matplotlib --hidden-import=matplotlib.backends.backend_tkagg --hidden-import=mpl_toolkits.mplot3d --collect-data matplotlib exr_to_ies_gui.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败
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
echo EXE文件位置: dist\EXR_to_IES_Converter.exe
echo.
echo 注意：如果要读取EXR，需要安装：
echo   pip install OpenEXR
echo 或
echo   pip install Pillow
echo.

pause
