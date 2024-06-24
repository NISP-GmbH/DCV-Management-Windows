# Set the working directory
Set-Location -Path "@@AppPath@@"

# Run the Flask app
& "@@PythonPath@@\python.exe" "@@AppPath@@\app.py"
