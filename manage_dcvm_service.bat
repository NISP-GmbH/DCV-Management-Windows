@echo off
REM manage_dcvm_service.bat
REM This script stops, starts, or restarts the service using dcvm_service.py.
REM Usage: manage_dcvm_service.bat start | stop | restart

if "%~1"=="" (
    echo No command provided.
    echo Usage: %0 start ^| stop ^| restart
    goto end
)

REM Process the command-line parameter (case-insensitive)
if /I "%~1"=="stop" (
    echo Stopping DCVM Service...
    python dcvm_service.py stop
    if %errorlevel% neq 0 (
        echo Error stopping DCVM Service.
        goto end
    )
    echo DCVM Service stopped successfully.
    goto end
)

if /I "%~1"=="start" (
    echo Starting DCVM Service...
    python dcvm_service.py start
    if %errorlevel% neq 0 (
        echo Error starting DCVM Service.
        goto end
    )
    echo DCVM Service started successfully.
    goto end
)

if /I "%~1"=="restart" (
    echo Restarting DCVM Service...
    REM Stop the service
    python dcvm_service.py stop
    if %errorlevel% neq 0 (
        echo Error stopping DCVM Service.
        goto end
    )
    REM Wait a few seconds to ensure the service has stopped
    timeout /t 5 /nobreak >nul
    REM Start the service
    python dcvm_service.py start
    if %errorlevel% neq 0 (
        echo Error starting DCVM Service.
        goto end
    )
    echo DCVM Service restarted successfully.
    goto end
)

echo Invalid command: %~1
echo Usage: %0 start ^| stop ^| restart

:end
pause
