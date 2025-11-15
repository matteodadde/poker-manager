Write-Host "==> Impostazione AMBIENTE DI PRODUZIONE (Docker) <==" -ForegroundColor Cyan

# Pulizia variabili conflittuali
$vars = "FLASK_ENV", "DATABASE_URL", "REDIS_URL"
foreach ($v in $vars) {
    [System.Environment]::SetEnvironmentVariable($v, $null, "Process")
}

$envFile = ".\.env.production"

if (-Not (Test-Path $envFile)) {
    Write-Host "ERRORE: .env.production NON trovato!" -ForegroundColor Red
    exit 1
}

# Caricamento delle variabili
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*#") { return }
    if ($_ -match "^\s*$") { return }

    $parts = $_ -split "=", 2
    $key = $parts[0].Trim()
    $value = $parts[1].Trim()
    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
}

Write-Host "Ambiente di produzione impostato! Docker Compose puo' essere avviato." -ForegroundColor Green
