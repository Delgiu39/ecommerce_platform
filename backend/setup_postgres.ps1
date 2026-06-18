# setup_postgres.ps1
$ErrorActionPreference = "Stop"

$workspaceDir = "c:\Users\delgi\Desktop\Progetti CV\E-Commerce con Gateway di pagamento (Full-Stack)\backend"
$pgDir = "$workspaceDir\postgresql"
$zipFile = "$workspaceDir\postgresql.zip"
$downloadUrl = "https://get.enterprisedb.com/postgresql/postgresql-16.3-1-windows-x64-binaries.zip"

if (-not (Test-Path $pgDir)) {
    Write-Host "Creazione directory: $pgDir"
    New-Item -ItemType Directory -Force -Path $pgDir | Out-Null
}

# Scarica lo zip dei binari se non è già presente
if (-not (Test-Path $zipFile)) {
    Write-Host "Download dei binari di PostgreSQL (Portable ZIP) tramite curl..."
    curl.exe -L -o $zipFile $downloadUrl
}

# Estrai lo zip se la cartella pgsql non esiste
if (-not (Test-Path "$pgDir\pgsql")) {
    Write-Host "Estrazione dell'archivio PostgreSQL..."
    Expand-Archive -Path $zipFile -DestinationPath $pgDir -Force
}

$binDir = "$pgDir\pgsql\bin"
$dataDir = "$pgDir\data"

# Inizializza il database se la cartella data non esiste
if (-not (Test-Path $dataDir)) {
    Write-Host "Inizializzazione del cluster di database PostgreSQL..."
    $pwFile = "$pgDir\pw.txt"
    "postgres" | Out-File -FilePath $pwFile -Encoding ascii -NoNewline
    
    # Esegui initdb impostando la password di superuser 'postgres'
    & "$binDir\initdb.exe" -D $dataDir -U postgres -A scram-sha-256 --pwfile=$pwFile
    
    # Pulisci il file temporaneo della password
    Remove-Item $pwFile -Force
}

# Avvia PostgreSQL
Write-Host "Avvio del server PostgreSQL..."
& "$binDir\pg_ctl.exe" -D $dataDir -l "$pgDir\pg.log" start

# Attendi 4 secondi per l'avvio completo
Start-Sleep -Seconds 4

# Crea il database 'ecommerce_db'
Write-Host "Creazione del database 'ecommerce_db'..."
$env:PGPASSWORD = "postgres"
try {
    & "$binDir\createdb.exe" -U postgres -h localhost -p 5432 ecommerce_db
    Write-Host "Database 'ecommerce_db' creato con successo!"
} catch {
    Write-Host "Il database esiste già o si è verificato un avviso durante la creazione."
}

Write-Host "PostgreSQL Portable è pronto e in esecuzione sulla porta 5432!"
