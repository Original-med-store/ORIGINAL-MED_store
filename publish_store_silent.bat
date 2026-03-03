@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Configuration
if not exist "logs" mkdir "logs"
set LOG_FILE=logs\publish.log
echo %date% %time% - Atomic Sync Start > %LOG_FILE%

:: Forced Cleanup of any previous failed state
git rebase --abort >nul 2>&1
git am --abort >nul 2>&1

:: Aggressive Add and Commit
git add -A >> %LOG_FILE% 2>&1
git commit -m "Auto-update %date% %time%" >> %LOG_FILE% 2>&1

:: Fetch and Rebase with "Ours" strategy to prioritize local data files
git fetch origin main >> %LOG_FILE% 2>&1
git pull origin main --rebase -X ours >> %LOG_FILE% 2>&1

:: If still failed (due to unstaged changes during rebase), try one more time
if %errorlevel% neq 0 (
    echo [RETRY] Detected rebase failure, attempt forced sync >> %LOG_FILE%
    git add -A >> %LOG_FILE% 2>&1
    git pull origin main --rebase -X ours >> %LOG_FILE% 2>&1
)

:: Final Push
git push origin main >> %LOG_FILE% 2>&1

if %errorlevel% equ 0 (
    echo [SUCCESS] >> %LOG_FILE%
    exit /b 0
) else (
    echo [ERROR] %errorlevel% >> %LOG_FILE%
    exit /b 1
)
