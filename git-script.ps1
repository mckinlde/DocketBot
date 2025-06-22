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

Write-Host "Freezing pip dependencies..."
pip freeze > requirements.txt

$commitMsg = Read-Host "Enter Git commit message"

Write-Host "Adding all changes and committing to Git..."
git add -A
git commit -m "$commitMsg"

Write-Host "Pushing changes to remote..."
git push

Write-Host "Rebuilding executable with PyInstaller..."
pyinstaller DocketBot.spec

Write-Host "Done."
