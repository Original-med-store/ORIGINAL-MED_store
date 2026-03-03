@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Use a temporary log file to avoid file-locks if Python is reading the main one
set TEMP_LOG=logs\publish_temp.log
set FINAL_LOG=logs\publish.log

if not exist "logs" mkdir "logs"
echo %date% %time% - Atomic Sync Start > %TEMP_LOG%

:: Cleanup Git State
git rebase --abort >nul 2>&1
git am --abort >nul 2>&1

:: Remove logs from index permanently to stop conflicts
git rm --cached -r logs >> %TEMP_LOG% 2>&1

:: Stage and Commit
git add -A >> %TEMP_LOG% 2>&1
git commit -m "Auto-update %date% %time%" >> %TEMP_LOG% 2>&1

:: Sync with Remote
git fetch origin main >> %TEMP_LOG% 2>&1
git pull origin main --rebase --autostash -X ours >> %TEMP_LOG% 2>&1

:: Push
git push origin main >> %TEMP_LOG% 2>&1

set RE=0
if %errorlevel% equ 0 (
    echo [SUCCESS] >> %TEMP_LOG%
    set RE=0
) else (
    echo [CRITICAL ERROR] >> %TEMP_LOG%
    set RE=1
)

:: Swap logs only at the very end
type %TEMP_LOG% > %FINAL_LOG%
del %TEMP_LOG%

exit /b %RE%
