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

REM Install the combined DCV management service using pywin32
echo Installing DCV Management Service...
python dcvm_service.py --startup auto install
if %errorlevel% neq 0 (
    echo Error installing DCV Management Service.
    exit /b %errorlevel%
)

REM Start the DCV Management Service
echo Starting DCV Management Service...
python dcvm_service.py start
if %errorlevel% neq 0 (
    echo Error starting DCV Management Service.
    exit /b %errorlevel%
)

echo All scripts executed successfully.
