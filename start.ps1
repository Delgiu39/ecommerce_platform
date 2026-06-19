# start.ps1 - Script di avvio unificato per E-Commerce Platform
# Avvia PostgreSQL, Backend FastAPI e Frontend React con un unico comando

$ErrorActionPreference = "Continue"
$ScriptRoot = $PSScriptRoot

Clear-Host
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "       E-COMMERCE PAYMENT PLATFORM  -  AVVIO RAPIDO" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# FUNZIONE: Attende finche la porta TCP e in ascolto (max $MaxSeconds secondi)
# ---------------------------------------------------------------------------
function Wait-ForPort {
    param([int]$Port, [int]$MaxSeconds = 30)
    $elapsed = 0
    Write-Host "  Attendo che la porta $Port sia disponibile..." -ForegroundColor Gray -NoNewline
    while ($elapsed -lt $MaxSeconds) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", $Port)
            $tcp.Close()
            Write-Host " pronta!" -ForegroundColor Green
            return $true
        } catch {
            Start-Sleep -Seconds 1
            $elapsed++
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    }
    Write-Host " TIMEOUT!" -ForegroundColor Red
    return $false
}

# ---------------------------------------------------------------------------
# 1. VERIFICA PREREQUISITI
# ---------------------------------------------------------------------------
Write-Host "[1/5] Verifica dei prerequisiti..." -ForegroundColor Yellow

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRORE] Python non trovato nel PATH. Installa Python 3.11+ da https://python.org" -ForegroundColor Red
    Read-Host "Premi INVIO per uscire"
    Exit 1
}
$pyVer = python --version 2>&1
Write-Host "  [OK] $pyVer" -ForegroundColor Green

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[ERRORE] Node.js non trovato nel PATH. Installa Node.js 18+ da https://nodejs.org" -ForegroundColor Red
    Read-Host "Premi INVIO per uscire"
    Exit 1
}
$nodeVer = node --version 2>&1
Write-Host "  [OK] Node.js $nodeVer" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. CONFIGURAZIONE BACKEND
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/5] Configurazione ambiente Backend..." -ForegroundColor Yellow

$backendDir = Join-Path $ScriptRoot "backend"

if (-not (Test-Path (Join-Path $backendDir "venv"))) {
    Write-Host "  Creazione ambiente virtuale Python..." -ForegroundColor Gray
    python -m venv (Join-Path $backendDir "venv")
}
Write-Host "  [OK] Ambiente virtuale Python pronto." -ForegroundColor Green

$pip = Join-Path $backendDir "venv\Scripts\pip.exe"
Write-Host "  Installazione/Aggiornamento dipendenze backend..." -ForegroundColor Gray
$pipResult = & cmd /c "`"$backendDir\venv\Scripts\pip.exe`" install -r `"$backendDir\requirements.txt`" 2>&1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [INFO] pip install fallito - ricreo il venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force (Join-Path $backendDir "venv")
    python -m venv (Join-Path $backendDir "venv")
    & cmd /c "`"$backendDir\venv\Scripts\pip.exe`" install -r `"$backendDir\requirements.txt`" 2>&1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRORE] Impossibile installare le dipendenze anche dopo aver ricreato il venv." -ForegroundColor Red
        Read-Host "Premi INVIO per uscire"; Exit 1
    }
}
Write-Host "  [OK] Dipendenze backend aggiornate." -ForegroundColor Green

$envFile    = Join-Path $backendDir ".env"
$envExample = Join-Path $backendDir ".env.example"
if (-not (Test-Path $envFile)) {
    Write-Host "  File .env non trovato - copio da .env.example e genero SECRET_KEY..." -ForegroundColor Gray
    Copy-Item $envExample $envFile
    $secretKey = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
    (Get-Content $envFile) -replace "SECRET_KEY=.*", "SECRET_KEY=$secretKey" | Set-Content $envFile
}
Write-Host "  [OK] File .env presente." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 3. CONFIGURAZIONE FRONTEND
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/5] Configurazione ambiente Frontend..." -ForegroundColor Yellow

$frontendDir = Join-Path $ScriptRoot "frontend"

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "  Installazione dipendenze npm (potrebbe richiedere 1-2 minuti)..." -ForegroundColor Gray
    Push-Location $frontendDir
    npm install --silent
    Pop-Location
}
Write-Host "  [OK] Dipendenze frontend pronte." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 4. AVVIO POSTGRESQL
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/5] Avvio del database PostgreSQL..." -ForegroundColor Yellow

$pgBin  = Join-Path $backendDir "postgresql\pgsql\bin"
$pgData = Join-Path $backendDir "postgresql\data"
$pgLog  = Join-Path $backendDir "postgresql\pg.log"
$pgCtl  = Join-Path $pgBin "pg_ctl.exe"

$env:PGPASSWORD = "postgres"

# pg_ctl start -w avvia postgres come processo daemon indipendente dalla console
# e aspetta che sia pronto prima di restituire il controllo
Write-Host "  Avvio di PostgreSQL tramite pg_ctl (attendo che sia pronto)..." -ForegroundColor Gray
$pgCtlResult = & cmd /c "`"$pgCtl`" -D `"$pgData`" -l `"$pgLog`" -w start 2>&1"
if ($LASTEXITCODE -ne 0) {
    # pg_ctl puo' restituire errore se postgres era gia' in esecuzione
    $statusResult = & cmd /c "`"$pgCtl`" -D `"$pgData`" status 2>&1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRORE] PostgreSQL non si e' avviato correttamente." -ForegroundColor Red
        Write-Host "         Controlla il log: $pgLog" -ForegroundColor Red
        Read-Host "Premi INVIO per uscire"
        Exit 1
    }
    Write-Host "  [INFO] PostgreSQL era gia' in esecuzione." -ForegroundColor Gray
}
Write-Host "  [OK] PostgreSQL pronto sulla porta 5432." -ForegroundColor Green

# Crea il database ecommerce_db se non esiste gia
$createDb = Join-Path $pgBin "createdb.exe"
& cmd /c "`"$createDb`" -U postgres -h 127.0.0.1 -p 5432 ecommerce_db 2>nul" | Out-Null
Write-Host "  [OK] Database 'ecommerce_db' pronto." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 5. AVVIO BACKEND E FRONTEND
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/5] Avvio dei servizi applicativi..." -ForegroundColor Yellow

# Backend FastAPI in una nuova finestra PowerShell
$backendCmd = "Set-Location '$backendDir'; .\venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Write-Host "  Attendo che il backend FastAPI risponda sulla porta 8000..." -ForegroundColor Gray
$backendReady = Wait-ForPort -Port 8000 -MaxSeconds 45
if (-not $backendReady) {
    Write-Host "  [ATTENZIONE] Il backend non ha risposto entro 45s. Potrebbe essere ancora in avvio." -ForegroundColor Yellow
}

# Frontend Vite in una nuova finestra PowerShell
$frontendCmd = "Set-Location '$frontendDir'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "  Attendo che il frontend Vite risponda sulla porta 5173..." -ForegroundColor Gray
$frontendReady = Wait-ForPort -Port 5173 -MaxSeconds 30
if (-not $frontendReady) {
    Write-Host "  [ATTENZIONE] Il frontend non ha risposto entro 30s. Potrebbe essere ancora in avvio." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# RIEPILOGO FINALE
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=======================================================================" -ForegroundColor Green
Write-Host "                    APPLICAZIONE AVVIATA!" -ForegroundColor Green
Write-Host "=======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend React   -> http://localhost:5173" -ForegroundColor Cyan
Write-Host "  API Backend      -> http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  Swagger Docs     -> http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  [INFO] Apertura del browser automatica..." -ForegroundColor Gray
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "  PostgreSQL e in esecuzione come daemon in background." -ForegroundColor Gray
Write-Host "  Premi INVIO per arrestare PostgreSQL e chiudere questa sessione." -ForegroundColor Yellow
Write-Host "  (Backend e Frontend: chiudi manualmente le loro finestre con Ctrl+C)" -ForegroundColor Gray
Write-Host ""
Read-Host "Premi INVIO per terminare"

# Spegni PostgreSQL in modo pulito
Write-Host ""
Write-Host "[*] Arresto di PostgreSQL..." -ForegroundColor Yellow
& cmd /c "`"$pgCtl`" -D `"$pgData`" stop -m fast 2>&1" | Out-Null
Write-Host "[OK] PostgreSQL arrestato. Ciao!" -ForegroundColor Green
Start-Sleep -Seconds 1
