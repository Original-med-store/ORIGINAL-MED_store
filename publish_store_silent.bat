@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Radical Reset: Moving logs to system TEMP to avoid file locks and Git conflicts
set LOG_DIR=%TEMP%\original-med-logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\publish_last.log

echo %date% %time% - Radical Sync Start > "%LOG_FILE%"

:: 1. Force Break any Git Deadlocks (Rebase, Merge, AM)
if exist ".git\rebase-merge" rmdir /s /q ".git\rebase-merge" >> "%LOG_FILE%" 2>&1
if exist ".git\rebase-apply" rmdir /s /q ".git\rebase-apply" >> "%LOG_FILE%" 2>&1
if exist ".git\MERGE_HEAD" del /f /q ".git\MERGE_HEAD" >> "%LOG_FILE%" 2>&1
git rebase --abort >nul 2>&1
git merge --abort >nul 2>&1

:: 2. Clean Index from any accidentally tracked log files
git rm --cached -r logs >nul 2>&1

:: 3. Aggressive Stage and Commit
git add -A >> "%LOG_FILE%" 2>&1
git commit -m "Auto-update %date% %time%" >> "%LOG_FILE%" 2>&1

:: 4. Forced Sync Sequence
git fetch origin main >> "%LOG_FILE%" 2>&1

:: Use a hard reset strategy if pull rebase fails (The Radical Solution)
git pull origin main --rebase --autostash -X ours >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    echo [RECOVERY] Pull failed, attempting hard recovery >> "%LOG_FILE%"
    git add -A >> "%LOG_FILE%" 2>&1
    git rebase --skip >> "%LOG_FILE%" 2>&1
    git pull origin main --rebase --autostash -X ours >> "%LOG_FILE%" 2>&1
)

:: 5. Final Push
git push origin main >> "%LOG_FILE%" 2>&1

if %errorlevel% equ 0 (
    echo [SUCCESS] >> "%LOG_FILE%"
    exit /b 0
) else (
    echo [FATAL ERROR] >> "%LOG_FILE%"
    exit /b 1
)
