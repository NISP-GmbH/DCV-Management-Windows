# Define service and task names
$services = @(
    @{
        ServiceName = "DCV Management Service"
        TaskName = "DCV Management"
    },
    @{
        ServiceName = "DCV Session Monitor Service"
        TaskName = "DCV Session Monitor"
    }
)

foreach ($service in $services) {
    $serviceName = $service.ServiceName
    $taskName = $service.TaskName

    Write-Host "Processing service '$serviceName' and task '$taskName'..."

    # Check if the service exists
    $serviceExists = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

    if ($serviceExists) {
        # Try to disable and stop the service
        try {
            Set-Service -Name $serviceName -StartupType Disabled -ErrorAction Stop
            Stop-Service -Name $serviceName -Force -ErrorAction Stop
            Write-Host "Service '$serviceName' has been disabled and stopped."
        }
        catch {
            Write-Host "Failed to disable or stop service '$serviceName'. Error: $_"
        }

        # Try to remove the service
        try {
            sc.exe delete $serviceName
            Write-Host "Service '$serviceName' has been removed."
        }
        catch {
            Write-Host "Failed to remove service '$serviceName'. Error: $_"
        }
    }
    else {
        Write-Host "Service '$serviceName' not found."
    }

    # Remove the scheduled task
    $taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

    if ($taskExists) {
        try {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            Write-Host "Scheduled task '$taskName' has been removed."
        }
        catch {
            Write-Host "Failed to remove scheduled task '$taskName'. Error: $_"
        }
    }
    else {
        Write-Host "Scheduled task '$taskName' not found."
    }

    Write-Host "Process completed for service '$serviceName' and task '$taskName'."
    Write-Host "---"
}

Write-Host "All services and scheduled tasks removal process completed."
