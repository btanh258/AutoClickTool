@echo off
chcp 65001 >nul
setlocal
echo ==========================================
echo      BUILD AUTOCLICK TOOL 1.1.3 (EXE)
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
echo [OK] File exe: dist\AutoClickTool.exe
powershell -NoProfile -Command "Compress-Archive -Path 'dist\AutoClickTool.exe','README.md' -DestinationPath 'AutoClickTool-1.1.3.zip' -Force"
echo [OK] File zip: AutoClickTool-1.1.3.zip
echo.
echo Upload ca 2 file (exe + zip) len release GitHub v1.1.0
echo de tinh nang tu cap nhat trong app tim thay file exe.
pause
