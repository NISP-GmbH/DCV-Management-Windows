# Function to read INI file
function Get-IniContent ($filePath) {
    $ini = @{}
    switch -regex -file $filePath {
        "^\[(.+)\]" {
            $section = $matches[1]
            $ini[$section] = @{}
        }
        "(.+)=(.+)" {
            $name, $value = $matches[1..2]
            $ini[$section][$name] = $value.Trim()
        }
    }
    return $ini
}

# Read the INI file from the current directory
$iniPath = Join-Path $PWD.Path "settings.ini"
if (-not (Test-Path $iniPath)) {
    Write-Host "Error: settings.ini not found in the current directory."
    exit 1
}
$iniContent = Get-IniContent $iniPath

# Extract the required paths
$pythonPath = $iniContent["Service"]["PythonPath"]
$appPath = $iniContent["Service"]["AppPath"]
$dcvPath = $iniContent["Service"]["DcvPath"]

# Remove "dcv.exe" from dcvPath
$dcvPath = Split-Path -Parent $dcvPath

# Function to add a path to the system PATH if it's not already there
function Add-ToPath($newPath) {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    if ($currentPath -notlike "*$newPath*") {
        $newSystemPath = $currentPath + ";" + $newPath
        [Environment]::SetEnvironmentVariable("Path", $newSystemPath, "Machine")
        Write-Host "Added $newPath to system PATH"
    } else {
        Write-Host "$newPath is already in system PATH"
    }
}

# Set PythonPath
[Environment]::SetEnvironmentVariable("PythonPath", $pythonPath, "Machine")
Write-Host "Set PythonPath to $pythonPath"

# Set AppPath
[Environment]::SetEnvironmentVariable("AppPath", $appPath, "Machine")
Write-Host "Set AppPath to $appPath"

# Add paths to system PATH
Add-ToPath $pythonPath
Add-ToPath $appPath
Add-ToPath $dcvPath

Write-Host "Environment variables have been updated. You may need to restart your PowerShell session or computer for changes to take effect."
