# Function to read INI file
function Get-IniContent {
    param (
        [string]$Path
    )

    $ini = @{}
    $section = ""
    foreach ($line in Get-Content $Path) {
        $line = $line.Trim()
        if ($line -match '^\[(.+)\]$') {
            $section = $matches[1]
            $ini[$section] = @{}
        } elseif ($line -match '^\s*([^=]+?)\s*=\s*(.*?)\s*$') {
            $name, $value = $matches[1], $matches[2]
            $ini[$section][$name] = $value
        }
    }
    return $ini
}

# Read settings.ini to get AppPath variable
$iniPath = "settings.ini"
$config = Get-IniContent $iniPath

$appPath = $config["Service"]["AppPath"]

if (-not (Test-Path $appPath)) {
    Write-Error "AppPath '$appPath' does not exist."
    exit 1
}

# Define the script to run every minute
$scriptPath = Join-Path $appPath "invoke_api.ps1"

if (-not (Test-Path $scriptPath)) {
    Write-Error "Script '$scriptPath' does not exist."
    exit 1
}

# Create a log directory
$logDir = Join-Path $appPath "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

# Define the task trigger - every 1 minute
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration ([TimeSpan]::FromDays(365 * 10))

# Define the task action - run PowerShell script with logging
$logFile = Join-Path $logDir "invoke_api_log.txt"
$actionArgument = "-ExecutionPolicy Bypass -File `"$scriptPath`" *>> `"$logFile`" 2>&1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgument

# Define the principal - run with highest privileges
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Define the task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Unregister existing task if it exists
Unregister-ScheduledTask -TaskName "InvokeDcvManagementScript" -Confirm:$false -ErrorAction SilentlyContinue

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName "InvokeDcvManagementScript" -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Description "Runs invoke_api.ps1 every minute"
    Write-Output "Scheduled task 'InvokeDcvManagementScript' created successfully."
} catch {
    Write-Error "Failed to create scheduled task: $_"
    exit 1
}

# Verify the scheduled task
try {
    $task = Get-ScheduledTask -TaskName "InvokeDcvManagementScript" -ErrorAction Stop
    if ($task) {
        Write-Output "Scheduled task 'InvokeDcvManagementScript' is verified."
        
        # Start the task immediately
        Start-ScheduledTask -TaskName "InvokeDcvManagementScript"
        Write-Output "Scheduled task 'InvokeDcvManagementScript' has been started."
    } else {
        Write-Error "Scheduled task 'InvokeDcvManagementScript' not found."
    }
} catch {
    Write-Error "Error verifying scheduled task: $_"
}

Write-Output "Setup completed. Check the log file at $logFile for task execution details."
