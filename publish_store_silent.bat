@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Force cleanup of any stuck git states or offending logs
git rebase --abort >nul 2>&1
git rm -f publish.log store_publish.log >nul 2>&1
if not exist "logs" mkdir "logs"

set LOG_FILE=logs\publish.log
echo %date% %time% - Starting atomic publish... > %LOG_FILE%

:: Ensure we are on main and clean
git fetch origin main >> %LOG_FILE% 2>&1
git add . >> %LOG_FILE% 2>&1
git commit -m "Auto-update from Store Manager" >> %LOG_FILE% 2>&1

:: Pull with 'ours' strategy for logs/metadata but keep local for code/data
git pull origin main --rebase -X ours >> %LOG_FILE% 2>&1

:: Final Push
git push origin main >> %LOG_FILE% 2>&1

if %errorlevel% equ 0 (
    echo %date% %time% - SUCCESS >> %LOG_FILE%
    exit /b 0
) else (
    echo %date% %time% - FAILED >> %LOG_FILE%
    exit /b 1
)
