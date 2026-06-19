@echo off
title E-Commerce Platform - Avvio Rapido
cls

echo =======================================================================
echo        E-COMMERCE PAYMENT PLATFORM  -  AVVIO RAPIDO
echo =======================================================================
echo.

:: -----------------------------------------------------------------------
:: 1. VERIFICA PREREQUISITI
:: -----------------------------------------------------------------------
echo [1/5] Verifica dei prerequisiti...

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERRORE] Python non trovato nel PATH!
    echo          Installa Python 3.11+ da https://python.org e riprova.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do set PY_VER=%%V
echo   [OK] %PY_VER%

where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERRORE] Node.js non trovato nel PATH!
    echo          Installa Node.js 18+ da https://nodejs.org e riprova.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('node --version 2^>^&1') do set NODE_VER=%%V
echo   [OK] Node.js %NODE_VER%

:: -----------------------------------------------------------------------
:: 2. CONFIGURAZIONE BACKEND
:: -----------------------------------------------------------------------
echo.
echo [2/5] Configurazione ambiente Backend...

if not exist "backend\venv" (
    echo   Creazione ambiente virtuale Python...
    python -m venv backend\venv
    if %ERRORLEVEL% neq 0 (
        echo [ERRORE] Impossibile creare l'ambiente virtuale.
        pause
        exit /b 1
    )
)
echo   [OK] Ambiente virtuale Python pronto.

echo   Installazione/Aggiornamento dipendenze backend...
cmd /c "backend\venv\Scripts\pip.exe install -r backend\requirements.txt 2>&1"
if %ERRORLEVEL% neq 0 (
    echo   [INFO] Prima installazione fallita - ricreo l'ambiente virtuale...
    rmdir /s /q backend\venv
    python -m venv backend\venv
    cmd /c "backend\venv\Scripts\pip.exe install -r backend\requirements.txt 2>&1"
    if %ERRORLEVEL% neq 0 (
        echo [ERRORE] Impossibile installare le dipendenze anche dopo aver ricreato il venv.
        pause
        exit /b 1
    )
)
echo   [OK] Dipendenze backend pronte.

if not exist "backend\.env" (
    echo   File .env non trovato - copio da .env.example...
    copy "backend\.env.example" "backend\.env" >nul
    backend\venv\Scripts\python.exe -c "import secrets,re; path='backend/.env'; c=open(path).read(); open(path,'w').write(re.sub(r'SECRET_KEY=.*','SECRET_KEY='+secrets.token_hex(32),c))"
    echo   [OK] File .env creato con SECRET_KEY generata automaticamente.
) else (
    echo   [OK] File backend\.env gia presente.
)

:: -----------------------------------------------------------------------
:: 3. CONFIGURAZIONE FRONTEND
:: -----------------------------------------------------------------------
echo.
echo [3/5] Configurazione ambiente Frontend...

if not exist "frontend\node_modules" (
    echo   Installazione dipendenze npm ^(potrebbe richiedere 1-2 minuti^)...
    cd frontend
    call npm install --silent
    cd ..
    if %ERRORLEVEL% neq 0 (
        echo [ERRORE] npm install fallito.
        pause
        exit /b 1
    )
)
echo   [OK] Dipendenze frontend pronte.

:: -----------------------------------------------------------------------
:: 4. AVVIO POSTGRESQL
:: -----------------------------------------------------------------------
echo.
echo [4/5] Avvio del database PostgreSQL...

set PGPASSWORD=postgres
set PG_BIN=%~dp0backend\postgresql\pgsql\bin
set PG_DATA=%~dp0backend\postgresql\data
set PG_LOG=%~dp0backend\postgresql\pg.log

:: Usa pg_ctl start con il flag -w (wait) che:
::  1. avvia postgres come processo daemon veramente indipendente dalla console
::  2. aspetta finche il server e pronto prima di restituire il controllo
::  3. non termina postgres quando questa finestra si chiude
echo   Avvio di PostgreSQL tramite pg_ctl (attendo che sia pronto)...
"%PG_BIN%\pg_ctl.exe" -D "%PG_DATA%" -l "%PG_LOG%" -w start
if %ERRORLEVEL% neq 0 (
    :: pg_ctl potrebbe restituire errore se era gia in esecuzione - controlliamo
    "%PG_BIN%\pg_ctl.exe" -D "%PG_DATA%" status >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [ERRORE] PostgreSQL non si e avviato correttamente.
        echo          Controlla il log: %PG_LOG%
        pause
        exit /b 1
    )
    echo   [INFO] PostgreSQL era gia in esecuzione.
)
echo   [OK] PostgreSQL pronto sulla porta 5432.

:: Crea il database se non esiste
"%PG_BIN%\createdb.exe" -U postgres -h 127.0.0.1 -p 5432 ecommerce_db >nul 2>nul
echo   [OK] Database 'ecommerce_db' pronto.

:: -----------------------------------------------------------------------
:: 5. AVVIO BACKEND E FRONTEND IN FINESTRE SEPARATE
:: -----------------------------------------------------------------------
echo.
echo [5/5] Avvio dei servizi applicativi...

start "FastAPI Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
echo   [OK] Finestra Backend avviata.

:: Breve pausa per dare tempo al backend di partire
timeout /t 5 /nobreak >nul

start "React Frontend" cmd /k "cd frontend && npm run dev"
echo   [OK] Finestra Frontend avviata.

:: -----------------------------------------------------------------------
:: RIEPILOGO
:: -----------------------------------------------------------------------
echo.
echo =======================================================================
echo                    APPLICAZIONE AVVIATA!
echo =======================================================================
echo.
echo   Frontend React   -^>  http://localhost:5173
echo   API Backend      -^>  http://127.0.0.1:8000
echo   Swagger Docs     -^>  http://127.0.0.1:8000/docs
echo.
echo   Attendi qualche secondo che il backend carichi le migrazioni,
echo   poi apri http://localhost:5173 nel tuo browser.
echo.
echo =======================================================================
echo.
echo   Premi un tasto per arrestare PostgreSQL e chiudere questa finestra.
echo   (Backend e Frontend: chiudi manualmente le loro finestre con Ctrl+C)
echo.
pause >nul

:: -----------------------------------------------------------------------
:: SPEGNIMENTO POSTGRESQL
:: -----------------------------------------------------------------------
echo.
echo [*] Arresto di PostgreSQL...
"%PG_BIN%\pg_ctl.exe" -D "%PG_DATA%" stop -m fast >nul 2>nul
echo [OK] PostgreSQL arrestato. Ciao!
timeout /t 2 >nul
