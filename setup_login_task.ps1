# Read and parse the settings.ini file
$iniContent = Get-Content "settings.ini" -Raw
$config = @{}
$currentSection = ""

foreach ($line in $iniContent -split "`r`n") {
    if ($line -match '^\[(.+)\]$') {
        $currentSection = $matches[1]
        $config[$currentSection] = @{}
    }
    elseif ($line -match '^(.+?)=(.*)$') {
        $config[$currentSection][$matches[1]] = $matches[2]
    }
}

# Extract necessary paths
$appPath = $config['Service']['AppPath']
$pythonPath = $config['Service']['PythonPath']

# Define paths
$createSessionScript = Join-Path $appPath "create_dcv_session.ps1"
$pythonExe = Join-Path $pythonPath "python.exe"

# Create the scheduled task
$taskName = "DCV Login Task"
$taskDescription = "Create DCV session on user login"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$createSessionScript`""

# Register the task
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Description $taskDescription -RunLevel Highest -Force

Write-Host "Login task created successfully."
