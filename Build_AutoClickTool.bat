@echo off
chcp 65001 >nul
setlocal
echo ==========================================
echo      BUILD AUTOCLICK TOOL 1.1.8 (EXE - ONEDIR)
echo ==========================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Chua co Python. Chay Install_AutoClickTool.bat truoc.
    pause
    exit /b 1
)
python -m pip install --upgrade pyinstaller >nul 2>&1
python -m PyInstaller --noconfirm AutoClickTool.spec
if %errorlevel% neq 0 (
    echo [!] Build that bai.
    pause
    exit /b 1
)
echo.
echo [OK] File exe: dist\AutoClickTool\AutoClickTool.exe (onedir)
powershell -NoProfile -Command "Compress-Archive -Path 'dist\AutoClickTool' -DestinationPath 'AutoClickTool-v1.1.8.zip' -Force"
echo [OK] File zip: AutoClickTool-v1.1.8.zip
echo.
echo Upload file zip len release GitHub v1.1.8.
echo Nguoi dung giai nen zip roi chay exe trong thu muc AutoClickTool.
pause
