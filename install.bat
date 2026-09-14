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

REM Add to PATH suggestion
set INSTALL_DIR=%CD%

echo The 'bashmess' command is ready to use!
echo.
echo Option 1 - Run from this directory:
echo   cd %INSTALL_DIR%
echo   bashmess
echo.
echo Option 2 - Add to system PATH (run as Administrator):
echo   setx /M PATH "%%PATH%%;%INSTALL_DIR%"
echo   Then restart PowerShell/CMD and run: bashmess
echo.
echo Option 3 - Create desktop shortcut:
echo   Right-click bashmess.bat ^> Send to ^> Desktop
echo.
pause
