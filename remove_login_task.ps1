$taskName = "DCV Login Task"

# Check if the task exists
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($task) {
    # If the task exists, unregister it
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "The task '$taskName' has been successfully removed."
} else {
    Write-Host "The task '$taskName' does not exist."
}
