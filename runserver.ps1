# =====================================
#  Django AutoCAD System Launcher (Hidden)
# =====================================

$projectPath = "D:\xamp\htdocs\autocad_system"
$venvPath = "$projectPath\venv\Scripts\Activate.ps1"

# Go to project directory
Set-Location $projectPath

# Activate virtual environment
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..."
    & $venvPath
} else {
    Write-Host "No virtual environment found, continuing..."
}

# Start the Django server in Hidden mode
Write-Host "Starting Django development server (hidden window)..."
Start-Process powershell -WindowStyle Hidden -ArgumentList "-ExecutionPolicy Bypass", "-Command", "cd $projectPath; python manage.py runserver 0.0.0.0:8000"

# Optional: open the site in your browser automatically
Start-Process "http://127.0.0.1:8000/admin"
