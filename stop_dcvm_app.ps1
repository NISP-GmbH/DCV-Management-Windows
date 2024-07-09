# stop_dcvm_app.ps1

# Get all Python processes running app.py
$processes = Get-WmiObject Win32_Process | Where-Object {$_.Name -eq "python.exe" -and $_.CommandLine -like "*app.py*"}

if ($processes) {
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
    Write-Host "No DCV Management app processes found running."
}

Write-Host "DCV Management app termination process completed."
