@echo off
REM Bash Messenger Installer for Windows

echo ================================
echo   Bash Messenger Installer
echo ================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if errorlevel 1 (
    echo Error: Python 3.8 or higher is required
    python --version
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo √ Python %PYTHON_VERSION% detected

REM Check pip
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not installed
    pause
    exit /b 1
)

echo √ pip detected
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo × Installation failed
    echo Please check error messages above
    pause
    exit /b 1
)

echo.
echo ================================
echo √ Installation complete!
echo ================================
echo.

REM Get installation directory
set INSTALL_DIR=%CD%

echo The 'bashmess' command is ready!
echo.
echo To run Bash Messenger:
echo   1. From this directory: bashmess
echo   2. From anywhere: Add to PATH (see below)
echo.
echo === ADD TO PATH (Run PowerShell as Administrator) ===
echo [System.Environment]::SetEnvironmentVariable('Path', [System.Environment]::GetEnvironmentVariable('Path', 'User') + ';%INSTALL_DIR%', 'User')
echo.
echo Then restart your terminal and run: bashmess
echo.
echo === OR CREATE ALIAS IN POWERSHELL ===
echo echo "function bashmess { python '%INSTALL_DIR%\bash_messenger.py' $args }" ^>^> $PROFILE
echo Then restart PowerShell and run: bashmess
echo.
echo === OR RUN DIRECTLY ===
echo cd %INSTALL_DIR%
echo bashmess
echo.
pause
