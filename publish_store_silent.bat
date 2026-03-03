@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Initial cleanup to avoid rebase traps
git rebase --abort >nul 2>&1
git am --abort >nul 2>&1

:: Configure Git to ignore changes in logs if they made it to the index previously
git rm --cached -r logs >nul 2>&1

:: Aggressive Prep
git add . >> logs\publish.log 2>&1
git commit -m "Auto-update %date% %time%" >> logs\publish.log 2>&1

:: Forced Fetch
git fetch origin main >> logs\publish.log 2>&1

:: Attempt pull with rebase
:: We use --autostash to handle ANY occasional dirty state
git pull origin main --rebase --autostash -X ours >> logs\publish.log 2>&1

:: Triple check push
git push origin main >> logs\publish.log 2>&1

if %errorlevel% equ 0 (
    echo [SUCCESS] >> logs\publish.log
    exit /b 0
) else (
    echo [CRITICAL ERROR] >> logs\publish.log
    exit /b 1
)
