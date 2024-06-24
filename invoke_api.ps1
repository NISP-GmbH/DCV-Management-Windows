# invoke_api.ps1

# Set the URL of your Flask application
$url = "http://localhost:5000/check-all-sessions"

# Send a GET request to the /echo endpoint
try {
    $response = Invoke-RestMethod -Uri $url -Method Get -ContentType "application/json"

    # Display the response
    Write-Host "Response received:"
    Write-Host "stdout: $($response.stdout)"
    Write-Host "stderr: $($response.stderr)"
    Write-Host "returncode: $($response.returncode)"
}
catch {
    Write-Host "An error occurred: $_"
}
