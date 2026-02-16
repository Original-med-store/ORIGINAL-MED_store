@echo off
:: Add all changes
"C:\Program Files\Git\cmd\git.exe" add .

:: Commit changes
"C:\Program Files\Git\cmd\git.exe" commit -m "Auto-update from Store Manager"

:: Push changes
"C:\Program Files\Git\cmd\git.exe" push origin main
