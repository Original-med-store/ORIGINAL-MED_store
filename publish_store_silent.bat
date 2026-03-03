@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: 1. Setup Isolated Logging
if not exist "logs" mkdir "logs"
set "LOG_FILE=logs\sync.log"
echo %date% %time% - Nuclear Sync Initiated > "%LOG_FILE%"

:: 2. Emergency Git Cleanup
git rebase --abort >nul 2>&1
git merge --abort >nul 2>&1
if exist ".git\rebase-merge" rmdir /s /q ".git\rebase-merge" >> "%LOG_FILE%" 2>&1
if exist ".git\rebase-apply" rmdir /s /q ".git\rebase-apply" >> "%LOG_FILE%" 2>&1

:: 3. Ensure Logs are Never Tracked
git rm --cached -r logs >nul 2>&1
git rm --cached sync_status.log >nul 2>&1

:: 4. Atomic Commit
git add . >> "%LOG_FILE%" 2>&1
git commit -m "Auto-sync %date% %time%" >> "%LOG_FILE%" 2>&1

:: 5. High-Intensity Sync
echo Attempting Pull... >> "%LOG_FILE%"
git fetch origin main >> "%LOG_FILE%" 2>&1
git pull origin main --rebase --autostash -X ours >> "%LOG_FILE%" 2>&1

:: 6. Push with Force Fallback
echo Attempting Push... >> "%LOG_FILE%"
git push origin main >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo standard push failed, attempting nuclear force push... >> "%LOG_FILE%"
    git push origin main --force >> "%LOG_FILE%" 2>&1
)

set RE=0
if %errorlevel% equ 0 (
    echo [SUCCESS] >> "%LOG_FILE%"
    exit /b 0
) else (
    echo [ERROR] %errorlevel% >> "%LOG_FILE%"
    exit /b 1
)

:: Swap logs only at the very end
type %TEMP_LOG% > %FINAL_LOG%
del %TEMP_LOG%

exit /b %RE%
