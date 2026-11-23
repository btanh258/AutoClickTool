@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo         CAI DAT AUTOCLICK TOOL 1.1.8
echo ==========================================
echo.

:: Kiem tra Python, neu chua co thi cai
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] May tinh chua cai dat Python.
    echo Dang tai Python 3.11.9 ve may... (vui long doi trong it phut)
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo Dang tien hanh cai dat Python (chay ngam)...
    start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    del python_installer.exe
    :: Python vua cai chua co trong PATH cua phien cmd nay: tim duong dan that
    set "PYEXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    if exist "!PYEXE!" (
        echo [OK] Da cai dat Python, dung duong dan moi cai de cai thu vien.
        set "PYCMD=!PYEXE!"
    ) else (
        echo [OK] Da cai dat Python. Hay dong cua so nay, mo lai cmd roi chay lai file .bat nay.
        pause
        exit /b 1
    )
) else (
    echo [OK] Python da san sang.
    set "PYCMD=python"
)
echo.

echo Cai dat thu vien...
%PYCMD% -m pip install --upgrade pip
%PYCMD% -m pip install customtkinter pynput pystray pillow
if %errorlevel% neq 0 (
    echo [!] Cai thu vien that bai. Kiem tra mang roi chay lai file .bat nay.
    pause
    exit /b 1
)

echo.
echo Chay thu: %PYCMD% AutoClickTool.pyw
echo (Hoac build file exe: chay Build_AutoClickTool.bat)
echo.
echo ==========================================
echo                HOAN TAT
echo ==========================================
pause
