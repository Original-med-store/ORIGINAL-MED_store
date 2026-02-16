@echo off

REM Check for py launcher first
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Starting Store Manager with Python Launcher...
    py manage_store.py
    pause
    exit /b
)

REM Check for python in PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Starting Store Manager with Python...
    python manage_store.py
    pause
    exit /b
)

echo Python is not installed or not found in PATH.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
pause
