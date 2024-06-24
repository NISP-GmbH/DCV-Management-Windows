# Define service and task names
$serviceName = "DCV Management Service"
$taskName = "DCV Management"

# Disable and stop the service
if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
    Set-Service -Name $serviceName -StartupType Disabled
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Write-Host "Service '$serviceName' has been disabled and stopped."
} else {
    Write-Host "Service '$serviceName' not found."
}

# Remove the service
if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
    sc.exe delete $serviceName
    Write-Host "Service '$serviceName' has been removed."
} else {
    Write-Host "Service '$serviceName' not found, no need to remove."
}

# Remove the scheduled task
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Scheduled task '$taskName' has been removed."
} else {
    Write-Host "Scheduled task '$taskName' not found."
}

Write-Host "Service and scheduled task removal process completed."
