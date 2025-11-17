Write-Host "Starting project cleanup..."

# Determine project root (where this script is located, or fallback to current directory)
$projectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
Write-Host "Project root: $projectRoot"

# Stop Python processes (in case venv is active)
$procs = Get-Process python -ErrorAction SilentlyContinue
if ($procs) {
    Write-Host "Stopping running Python processes..."
    taskkill /IM python.exe /F | Out-Null
}

# Remove virtual environments
Write-Host "Removing virtual environments..."
Remove-Item "$projectRoot\venv" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$projectRoot\.venv" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$projectRoot\env" -Recurse -Force -ErrorAction SilentlyContinue

# Remove Python bytecode caches
Write-Host "Removing __pycache__ folders..."
Get-ChildItem $projectRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

# Remove pytest cache
Write-Host "Removing .pytest_cache..."
Remove-Item "$projectRoot\.pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue

# Remove .benchmarks
Write-Host "Removing .benchmarks..."
Remove-Item "$projectRoot\.benchmarks" -Recurse -Force -ErrorAction SilentlyContinue

# Remove coverage reports
Write-Host "Removing coverage..."
Remove-Item "$projectRoot\htmlcov" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$projectRoot\.coverage" -Force -ErrorAction SilentlyContinue

# Remove node_modules
Write-Host "Removing node_modules..."
Remove-Item "$projectRoot\node_modules" -Recurse -Force -ErrorAction SilentlyContinue

# Remove build or dist if exist
Write-Host "Removing build/dist folders if present..."
Remove-Item "$projectRoot\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$projectRoot\dist" -Recurse -Force -ErrorAction SilentlyContinue

# Remove existing instance folder
Write-Host "Removing instance folder..."
Remove-Item "$projectRoot\instance" -Recurse -Force -ErrorAction Silently

Write-Host "Cleanup completed."
