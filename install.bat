@echo off
REM Execute PowerShell scripts

REM Set execution policy to bypass for the current process
powershell.exe -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"

REM Execute setup_environment.ps1
echo Executing setup_environment.ps1...
powershell.exe -File .\setup_environment.ps1
if %errorlevel% neq 0 (
    echo Error executing setup_environment.ps1
    exit /b %errorlevel%
)

REM Execute install_api_app.ps1
echo Executing install_api_app.ps1...
powershell.exe -File .\install_api_app.ps1
if %errorlevel% neq 0 (
    echo Error executing install_api_app.ps1
    exit /b %errorlevel%
)

REM Execute install_dcv_session_monitor.ps1
echo Executing install_dcv_session_monitor.ps1...
powershell.exe -File .\install_dcv_session_monitor.ps1
if %errorlevel% neq 0 (
    echo Error executing install_dcv_session_monitor.ps1
    exit /b %errorlevel%
)

REM Execute setup_task.ps1
echo Executing setup_task.ps1...
powershell.exe -File .\setup_task.ps1
if %errorlevel% neq 0 (
    echo Error executing setup_task.ps1
    exit /b %errorlevel%
)

echo All scripts executed successfully.
