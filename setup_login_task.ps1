# Function to read INI file
function Get-IniContent ($filePath) {
    $ini = @{}
    switch -regex -file $filePath {
        "^\[(.+)\]" { # Section
            $section = $matches[1]
            $ini[$section] = @{}
            $CommentCount = 0
        }
        "^(;.*)$" { # Comment
            $value = $matches[1]
            $CommentCount = $CommentCount + 1
            $name = "Comment" + $CommentCount
            $ini[$section][$name] = $value
        }
        "(.+?)\s*=(.*)" { # Key
            $name, $value = $matches[1..2]
            $ini[$section][$name] = $value
        }
    }
    return $ini
}

# Read and parse the settings.ini file
$iniPath = "settings.ini"
if (-not (Test-Path $iniPath)) {
    Write-Host "Error: settings.ini file not found in the current directory."
    exit
}

$config = Get-IniContent $iniPath

# Debug: Print the parsed config
Write-Host "Parsed config:"
$config | ConvertTo-Json | Write-Host

# Check if required settings exist
if (-not $config.ContainsKey('Service')) {
    Write-Host "Error: 'Service' section not found in settings.ini"
    exit
}

if (-not $config['Service'].ContainsKey('AppPath')) {
    Write-Host "Error: 'AppPath' not found in 'Service' section of settings.ini"
    exit
}

if (-not $config['Service'].ContainsKey('PythonPath')) {
    Write-Host "Error: 'PythonPath' not found in 'Service' section of settings.ini"
    exit
}

# Extract necessary paths
$appPath = $config['Service']['AppPath']
$pythonPath = $config['Service']['PythonPath']

Write-Host "AppPath: $appPath"
Write-Host "PythonPath: $pythonPath"

# Define paths
$createSessionScript = Join-Path $appPath "create_dcv_session.ps1"
$wrapperScript = Join-Path $appPath "wrapper_create_dcv_session.ps1"
$pythonExe = Join-Path $pythonPath "python.exe"

Write-Host "createSessionScript: $createSessionScript"
Write-Host "wrapperScript: $wrapperScript"
Write-Host "pythonExe: $pythonExe"

# Create the wrapper script
$wrapperContent = @"
`$logPath = Join-Path "$appPath" "logs"
if (-not (Test-Path `$logPath)) {
    New-Item -ItemType Directory -Path `$logPath | Out-Null
}

`$logFile = Join-Path `$logPath ("dcv_session_creation_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")

Start-Transcript -Path `$logFile

Write-Host "Starting DCV session creation at $(Get-Date)"

try {
    & "$createSessionScript"
}
catch {
    Write-Host "An error occurred: `$_"
}

Write-Host "DCV session creation completed at $(Get-Date)"

Stop-Transcript
"@

Set-Content -Path $wrapperScript -Value $wrapperContent

# Create the scheduled task
$taskName = "DCV Login Task"
$taskDescription = "Create DCV session on user login"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$wrapperScript`""

# Register the task
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Description $taskDescription -RunLevel Highest -Force

Write-Host "Login task created successfully."
