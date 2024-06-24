# Set execution policy to bypass for the current process
powershell.exe -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"

# Read the settings.ini file
$iniContent = Get-Content "settings.ini" -Raw

# Parse the INI content
$ini = @{}
switch -regex ($iniContent -split '\r?\n') {
    '^\[(.+)\]' {
        $section = $matches[1]
        $ini[$section] = @{}
    }
    '(.+)=(.+)' {
        $name, $value = $matches[1..2]
        $ini[$section][$name] = $value
    }
}

# Create a hashtable for replacements
$replacements = @{}
foreach ($key in $ini['Service'].Keys) {
    $replacements["@@$key@@"] = $ini['Service'][$key]
}

# Get all .ps1 files in the current directory
$psFiles = Get-ChildItem -Path . -Filter *.ps1

# Process each .ps1 file
foreach ($file in $psFiles) {
    $content = Get-Content $file.FullName -Raw
    
    # Perform replacements
    foreach ($key in $replacements.Keys) {
        $content = $content -replace [regex]::Escape($key), $replacements[$key]
    }
    
    # Write the modified content back to the file
    Set-Content -Path $file.FullName -Value $content
}

Write-Host "Replacement complete for all .ps1 files in the current directory."
