# Set the working directory
Set-Location -Path "@@AppPath@@"

# Set up logging
$logFile = "@@AppPath@@\dcv_session_monitor_log.txt"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "$timestamp - Starting DCV Session Monitor"

# Run the Python script
try {
    & "@@PythonPath@@\python.exe" "@@AppPath@@\dcv_session_monitor.py"
    Add-Content -Path $logFile -Value "$timestamp - DCV Session Monitor started successfully"
} catch {
    Add-Content -Path $logFile -Value "$timestamp - Error starting DCV Session Monitor: $_"
}
