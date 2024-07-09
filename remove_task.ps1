# Define the task name
$taskName = "InvokeDcvManagementScript"

# Check if the task exists
$taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($taskExists) {
    # Unregister (remove) the scheduled task
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Output "Scheduled task '$taskName' removed successfully."
    } catch {
        Write-Error "Failed to remove scheduled task: $_"
    }
} else {
    Write-Output "Scheduled task '$taskName' not found. No action needed."
}
