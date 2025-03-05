@echo off
REM Execute PowerShell uninstallation scripts

REM Set execution policy to bypass for the current process
powershell.exe -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"

REM Stop the service using the Python service script
echo Stopping DCV Management Service...
python dcvm_service.py stop
if %errorlevel% neq 0 (
    echo Error stopping DCV Management Service.
    exit /b %errorlevel%
)

REM Remove the service using the Python service script
echo Removing DCV Management Service...
python dcvm_service.py remove
if %errorlevel% neq 0 (
    echo Error removing DCV Management Service.
    exit /b %errorlevel%
)

echo DCV Management Service has been removed successfully.

echo All uninstallation scripts executed successfully.
