# stop_dcv_apps.ps1

$appNames = @("app.py", "dcv_session_monitor.py")

foreach ($appName in $appNames) {
    # Get all Python processes running the specified app
    $processes = Get-WmiObject Win32_Process | Where-Object {$_.Name -eq "python.exe" -and $_.CommandLine -like "*$appName*"}

    if ($processes) {
        Write-Host "Stopping processes for $appName..."
        foreach ($process in $processes) {
            Write-Host "Stopping process: $($process.ProcessId)"
            
            # Try to stop the process gracefully
            $process.Terminate()
            
            # Wait for up to 10 seconds for the process to stop
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            while (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue) {
                if ($stopwatch.Elapsed.TotalSeconds -gt 10) {
                    Write-Host "Process did not stop gracefully. Forcing termination."
                    Stop-Process -Id $process.ProcessId -Force
                    break
                }
                Start-Sleep -Milliseconds 500
            }
            
            Write-Host "Process $($process.ProcessId) has been stopped."
        }
    } else {
        Write-Host "No processes found running $appName."
    }
}

Write-Host "DCV apps termination process completed."
