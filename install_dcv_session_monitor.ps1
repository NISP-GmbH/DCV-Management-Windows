# Create a scheduled task to run the Flask app at system startup
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File @@AppPath@@\run_dcv_session_monitor.ps1"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName "DCV Session Monitor" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "Runs the DCV Session Monitor at startup"

Start-ScheduledTask -TaskName "DCV Session Monitor"

# Create a Windows service for the app
$serviceName = "DCV Session Monitor Service"
$displayName = "DCV Session Monitor Service"
$binaryPath = "powershell.exe -ExecutionPolicy Bypass -File C:\@@AppPath@@\run_dcv_session_monitor.ps1"

New-Service -Name $serviceName -DisplayName $displayName -BinaryPathName $binaryPath -StartupType Automatic

Write-Host "DCV Management scheduled task and Windows service have been created. The app will start automatically on next system boot."
