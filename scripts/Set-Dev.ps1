Write-Host "==> Impostazione AMBIENTE DI SVILUPPO (Windows/macOS) <==" -ForegroundColor Cyan

# Path del file .env.local
$envFile = ".env.local"

if (!(Test-Path $envFile)) {
    Write-Host "ERRORE: File .env.local non trovato!" -ForegroundColor Red
    exit 1
}

# Legge ogni riga e imposta le variabili
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*#") { return }   # Salta commenti
    if ($_ -match "^\s*$") { return }   # Salta righe vuote

    $parts = $_ -split "=", 2

    if ($parts.Length -eq 2) {
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        Set-Item -Path ("Env:" + $name) -Value $value
        Write-Host ("Impostata variabile: " + $name) -ForegroundColor Green
    }
}

Write-Host "Ambiente di sviluppo configurato correttamente." -ForegroundColor Yellow
