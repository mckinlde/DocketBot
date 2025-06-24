$ErrorActionPreference = "Stop"

if (-not $env:VIRTUAL_ENV) {
    $venvPath = Join-Path -Path $PSScriptRoot -ChildPath ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        Write-Host "Activating virtual environment..."
        & $venvPath
    } else {
        Write-Warning "Virtual environment not found at $venvPath. Please activate manually."
    }
} else {
    Write-Host "Virtual environment already activated."
}

Write-Host "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

Write-Host "Freezing pip dependencies..."
pip freeze > requirements.txt

$commitMsg = Read-Host "Enter Git commit message"

Write-Host "Adding all changes and committing to Git..."
git add -A
git commit -m "$commitMsg"

Write-Host "Pushing changes to remote..."
git push

Write-Host "Rebuilding executable with PyInstaller..."

if (Test-Path .\build) {
    Remove-Item -Recurse -Force .\build -ErrorAction SilentlyContinue
} else {
    Write-Host "Build folder does not exist, skipping removal."
}

if (Test-Path .\dist) {
    Remove-Item -Recurse -Force .\dist -ErrorAction SilentlyContinue
} else {
    Write-Host "Dist folder does not exist, skipping removal."
}

pyinstaller --clean DocketBot.spec

Write-Host "Done."
