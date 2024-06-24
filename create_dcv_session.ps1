# Read settings from the INI file
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

# Get the curl path from the settings
$curlPath = $config['Service']['CurlPath']

# Get the current user's username
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$username = ($currentUser -split '\\')[-1]

# Construct the curl command
$url = "http://localhost:5000/create-session?owner=$username"

# Execute the curl command
try {
    $result = & $curlPath -s -X GET $url
    
    # Parse the JSON response
    $response = $result | ConvertFrom-Json
    
    if ($response.message -eq "created") {
        Write-Host "DCV session created successfully for user: $username"
    } elseif ($response.message -eq "already exist.") {
        Write-Host "DCV session already exists for user: $username"
    } else {
        Write-Host "Unexpected response: $result"
    }
} catch {
    Write-Host "An error occurred while creating the DCV session: $_"
}

# Optional: Add a delay to keep the window open (useful for debugging)
# Start-Sleep -Seconds 10
