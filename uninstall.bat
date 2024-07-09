@echo off
REM Execute PowerShell uninstallation scripts

REM Set execution policy to bypass for the current process
powershell.exe -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"

REM Execute remove_services.ps1
echo Executing remove_services.ps1...
powershell.exe -File .\stop_dcvm_app.ps1
powershell.exe -File .\remove_services.ps1
if %errorlevel% neq 0 (
    echo Error executing remove_services.ps1
    exit /b %errorlevel%
)

REM Execute remove_task.ps1
echo Executing remove_task.ps1...
powershell.exe -File .\remove_task.ps1
if %errorlevel% neq 0 (
    echo Error executing remove_task.ps1
    exit /b %errorlevel%
)

echo All uninstallation scripts executed successfully.
