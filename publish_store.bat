@echo off
echo Publishing Store Updates...

:: Add all changes
"C:\Program Files\Git\cmd\git.exe" add .

:: Commit changes
set /p commit_msg="Enter description of changes (optional): "
if "%commit_msg%"=="" set commit_msg="Update store content"
"C:\Program Files\Git\cmd\git.exe" commit -m "%commit_msg%"

:: Push changes
echo Uploading to GitHub...
"C:\Program Files\Git\cmd\git.exe" push origin main

echo.
echo Store published successfully!
pause
