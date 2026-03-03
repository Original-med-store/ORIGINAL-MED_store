@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "LOG_FILE=sync_status.log"
echo %date% %time% - Nuclear Sync Start > "%LOG_FILE%"

:: Typos Check: Reset everything and call git explicitly
:: 1. Force Break any Git Deadlocks
git rebase --abort >nul 2>&1
git merge --abort >nul 2>&1
if exist ".git\rebase-merge" rmdir /s /q ".git\rebase-merge" >> "%LOG_FILE%" 2>&1
if exist ".git\rebase-apply" rmdir /s /q ".git\rebase-apply" >> "%LOG_FILE%" 2>&1

:: 2. Ensure log file is ignored
git rm --cached "%LOG_FILE%" >nul 2>&1

:: 3. Aggressive Stage and Commit
git add . >> "%LOG_FILE%" 2>&1
git commit -m "Auto-update %date% %time%" >> "%LOG_FILE%" 2>&1

:: 4. Forced Fetch and Rebase
git fetch origin main >> "%LOG_FILE%" 2>&1
git pull origin main --rebase --autostash -X ours >> "%LOG_FILE%" 2>&1

:: 5. Push
git push origin main >> "%LOG_FILE%" 2>&1

if %errorlevel% equ 0 (
    echo [SUCCESS] >> "%LOG_FILE%"
    exit /b 0
) else (
    echo [ERROR] %errorlevel% >> "%LOG_FILE%"
    exit /b 1
)
