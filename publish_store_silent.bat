@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Prepare
if not exist "logs" mkdir "logs"
set LOG_FILE=logs\publish.log
echo %date% %time% - Atomic Sync Start > %LOG_FILE%

:: Reset any failed rebase state
git rebase --abort >nul 2>&1

:: Commit changes IF any
git add . >> %LOG_FILE% 2>&1
git commit -m "Auto-update %date% %time%" >> %LOG_FILE% 2>&1

:: Pull & Rebase
git fetch origin main >> %LOG_FILE% 2>&1
git pull origin main --rebase -X ours >> %LOG_FILE% 2>&1

:: Push
git push origin main >> %LOG_FILE% 2>&1

if %errorlevel% equ 0 (
    echo [SUCCESS] >> %LOG_FILE%
    exit /b 0
) else (
    echo [ERROR] %errorlevel% >> %LOG_FILE%
    exit /b 1
)
