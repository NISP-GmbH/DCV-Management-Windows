Write-Host "Restarting DCV Management..."
Stop-ScheduledTask -TaskName "DCV Management"
Start-Sleep -Seconds 5  # Wait for 5 seconds to ensure the task has stopped
Start-ScheduledTask -TaskName "DCV Management"
Write-Host "DCV Management has been restarted."
