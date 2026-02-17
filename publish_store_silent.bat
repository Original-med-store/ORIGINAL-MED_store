@echo off
cd /d "%~dp0"
echo %date% %time% - Starting publish... >> publish.log

:: Try to find git
where git >nul 2>nul
if %errorlevel% equ 0 (
    set GIT_CMD=git
) else (
    if exist "C:\Program Files\Git\cmd\git.exe" (
        set GIT_CMD="C:\Program Files\Git\cmd\git.exe"
    ) else (
        echo %date% %time% - Git not found! >> publish.log
        exit /b 1
    )
)

:: Add all changes
%GIT_CMD% add . >> publish.log 2>&1

:: Commit changes
%GIT_CMD% commit -m "Auto-update from Store Manager" >> publish.log 2>&1

:: Push changes
%GIT_CMD% push origin main >> publish.log 2>&1

if %errorlevel% equ 0 (
    echo %date% %time% - Publish successful >> publish.log
) else (
    echo %date% %time% - Publish failed >> publish.log
)
