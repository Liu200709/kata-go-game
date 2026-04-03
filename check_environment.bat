@echo off

setlocal

echo 开始检测KataGo围棋人机对弈程序环境...
echo =========================================

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python已安装
    python --version
) else (
    echo ✗ Python未安装，请先安装Python 3.6+
    goto end
)

:: 检查Flask是否安装
python -m pip show flask >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Flask已安装
) else (
    echo ⚠ Flask未安装，启动时会自动安装
)

:: 检查必要文件
set required_files=katago.exe default_model.bin.gz default_gtp.cfg main.py
for %%f in (%required_files%) do (
    if exist "%%f" (
        echo ✓ %%f 存在
    ) else (
        echo ✗ %%f 不存在
        goto end
    )
)

echo =========================================
echo 环境检测完成，程序可以运行！
echo 请运行 start.bat 启动程序
echo =========================================

:end
pause
