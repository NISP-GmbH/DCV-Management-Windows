# Define the task name
$taskName = "InvokeDcvManagementScript"

# Unregister (remove) the scheduled task
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Output "Scheduled task '$taskName' removed successfully."
} catch {
    Write-Error "Failed to remove scheduled task: $_"
}
