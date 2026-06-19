#!/usr/bin/env bash
# start.sh — Script di avvio unificato per E-Commerce Platform
# Compatibile con: macOS (Homebrew) e Linux (apt/systemd)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Colori
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; GRAY='\033[0;37m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
info() { echo -e "  ${GRAY}[INFO]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[ATTENZIONE]${NC} $1"; }
err()  { echo -e "${RED}[ERRORE]${NC} $1"; }

clear
echo -e "${CYAN}=======================================================================${NC}"
echo -e "${CYAN}       E-COMMERCE PAYMENT PLATFORM  —  AVVIO RAPIDO (macOS/Linux)${NC}"
echo -e "${CYAN}=======================================================================${NC}"
echo ""

# Rileva il sistema operativo
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == "linux"* ]]; then
    OS_TYPE="linux"
fi

# ---------------------------------------------------------------------------
# 1. VERIFICA PREREQUISITI
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[1/5] Verifica dei prerequisiti...${NC}"

if ! command -v python3 &>/dev/null; then
    err "Python3 non trovato nel PATH."
    if [ "$OS_TYPE" = "macos" ]; then
        echo "  Installa con: brew install python3"
    else
        echo "  Installa con: sudo apt install python3 python3-venv python3-pip"
    fi
    exit 1
fi
ok "$(python3 --version)"

if ! command -v node &>/dev/null; then
    err "Node.js non trovato nel PATH."
    if [ "$OS_TYPE" = "macos" ]; then
        echo "  Installa con: brew install node"
    else
        echo "  Installa con: sudo apt install nodejs npm"
    fi
    exit 1
fi
ok "Node.js $(node --version)"

if ! command -v psql &>/dev/null && ! command -v pg_isready &>/dev/null; then
    err "PostgreSQL non trovato nel PATH."
    if [ "$OS_TYPE" = "macos" ]; then
        echo "  Installa con: brew install postgresql@16"
    else
        echo "  Installa con: sudo apt install postgresql postgresql-contrib"
    fi
    exit 1
fi
ok "PostgreSQL disponibile."

# ---------------------------------------------------------------------------
# 2. CONFIGURAZIONE BACKEND
# ---------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[2/5] Configurazione ambiente Backend...${NC}"

if [ ! -d "$BACKEND_DIR/venv" ]; then
    info "Creazione ambiente virtuale Python..."
    python3 -m venv "$BACKEND_DIR/venv"
fi
ok "Ambiente virtuale Python pronto."

info "Installazione/Aggiornamento dipendenze backend..."
"$BACKEND_DIR/venv/bin/pip" install -q --upgrade pip
"$BACKEND_DIR/venv/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"
ok "Dipendenze backend installate."

if [ ! -f "$BACKEND_DIR/.env" ]; then
    info "File .env non trovato — copia da .env.example..."
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    if [ "$OS_TYPE" = "macos" ]; then
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET/" "$BACKEND_DIR/.env"
    else
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET/" "$BACKEND_DIR/.env"
    fi
    ok "File .env creato con SECRET_KEY generata automaticamente."
else
    ok "File backend/.env già presente."
fi

# ---------------------------------------------------------------------------
# 3. CONFIGURAZIONE FRONTEND
# ---------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[3/5] Configurazione ambiente Frontend...${NC}"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    info "Installazione dipendenze npm (potrebbe richiedere 1-2 minuti)..."
    cd "$FRONTEND_DIR" && npm install --silent && cd "$SCRIPT_DIR"
fi
ok "Dipendenze frontend pronte."

# ---------------------------------------------------------------------------
# 4. AVVIO POSTGRESQL
# ---------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[4/5] Avvio del database PostgreSQL...${NC}"

pg_is_running() {
    pg_isready -h 127.0.0.1 -p 5432 -q 2>/dev/null
    return $?
}

if pg_is_running; then
    ok "PostgreSQL già in esecuzione sulla porta 5432."
else
    info "Avvio di PostgreSQL..."
    if [ "$OS_TYPE" = "macos" ]; then
        # Prova prima con brew services (Homebrew standard)
        if command -v brew &>/dev/null; then
            # Rileva la versione installata (pg@16, pg@14, ecc.)
            PG_SERVICE=$(brew services list 2>/dev/null | grep -i postgresql | head -1 | awk '{print $1}')
            if [ -n "$PG_SERVICE" ]; then
                brew services start "$PG_SERVICE" &>/dev/null || true
            else
                err "Nessun servizio PostgreSQL trovato in Homebrew."
                echo "  Installa con: brew install postgresql@16"
                exit 1
            fi
        fi
    elif [ "$OS_TYPE" = "linux" ]; then
        # Prova systemd, poi service
        if command -v systemctl &>/dev/null; then
            sudo systemctl start postgresql 2>/dev/null || \
            sudo systemctl start postgresql@16-main 2>/dev/null || true
        elif command -v service &>/dev/null; then
            sudo service postgresql start 2>/dev/null || true
        fi
    fi

    # Aspetta che PostgreSQL sia pronto (max 20 secondi)
    info "Attendo che PostgreSQL sia pronto..."
    WAIT=0
    until pg_is_running || [ $WAIT -ge 20 ]; do
        sleep 1
        WAIT=$((WAIT + 1))
        printf "."
    done
    echo ""

    if ! pg_is_running; then
        err "PostgreSQL non risponde entro 20 secondi."
        echo "  Avvia manualmente PostgreSQL e riprova."
        exit 1
    fi
fi

# Crea il database ecommerce_db se non esiste
if ! psql -h 127.0.0.1 -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw ecommerce_db; then
    # Prova con l'utente postgres; su Linux potrebbe servire sudo -u postgres
    createdb -h 127.0.0.1 -U postgres ecommerce_db 2>/dev/null || \
    sudo -u postgres createdb ecommerce_db 2>/dev/null || true
fi
ok "Database 'ecommerce_db' pronto."

# ---------------------------------------------------------------------------
# 5. AVVIO BACKEND E FRONTEND IN NUOVI TERMINALI
# ---------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[5/5] Avvio dei servizi applicativi...${NC}"

BACKEND_CMD="source '$BACKEND_DIR/venv/bin/activate' && cd '$BACKEND_DIR' && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
FRONTEND_CMD="cd '$FRONTEND_DIR' && npm run dev"

if [ "$OS_TYPE" = "macos" ]; then
    # Apre due tab nel terminale macOS
    osascript <<EOF
tell application "Terminal"
    activate
    do script "$BACKEND_CMD"
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "$FRONTEND_CMD" in front window
end tell
EOF
    ok "Terminali Backend e Frontend aperti."
elif [ "$OS_TYPE" = "linux" ]; then
    # Prova vari emulatori terminali comuni
    if command -v gnome-terminal &>/dev/null; then
        gnome-terminal -- bash -c "$BACKEND_CMD; exec bash" &
        gnome-terminal -- bash -c "$FRONTEND_CMD; exec bash" &
    elif command -v xterm &>/dev/null; then
        xterm -title "FastAPI Backend" -e bash -c "$BACKEND_CMD; bash" &
        xterm -title "React Frontend" -e bash -c "$FRONTEND_CMD; bash" &
    elif command -v konsole &>/dev/null; then
        konsole -e bash -c "$BACKEND_CMD; bash" &
        konsole -e bash -c "$FRONTEND_CMD; bash" &
    elif command -v tilix &>/dev/null; then
        tilix -e bash -c "$BACKEND_CMD; bash" &
        tilix -e bash -c "$FRONTEND_CMD; bash" &
    else
        # Fallback: avvia in background con log su file
        warn "Nessun emulatore terminale grafico trovato."
        info "Avvio backend e frontend in background con log su file..."
        bash -c "$BACKEND_CMD" > "$SCRIPT_DIR/backend.log" 2>&1 &
        BACKEND_PID=$!
        bash -c "$FRONTEND_CMD" > "$SCRIPT_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        echo "  Backend PID: $BACKEND_PID  (log: backend.log)"
        echo "  Frontend PID: $FRONTEND_PID  (log: frontend.log)"
    fi
    ok "Backend e Frontend avviati."
fi

# ---------------------------------------------------------------------------
# RIEPILOGO FINALE
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}=======================================================================${NC}"
echo -e "${GREEN}                     APPLICAZIONE AVVIATA!${NC}"
echo -e "${GREEN}=======================================================================${NC}"
echo ""
echo -e "  Frontend React   ->  ${CYAN}http://localhost:5173${NC}"
echo -e "  API Backend      ->  ${CYAN}http://127.0.0.1:8000${NC}"
echo -e "  Swagger Docs     ->  ${CYAN}http://127.0.0.1:8000/docs${NC}"
echo ""

# Apre il browser automaticamente
sleep 2
if [ "$OS_TYPE" = "macos" ]; then
    open "http://localhost:5173"
elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:5173" &>/dev/null &
fi

echo -e "${YELLOW}  Premi INVIO per arrestare PostgreSQL e terminare.${NC}"
echo -e "${GRAY}  (Backend e Frontend: chiudi le loro finestre con Ctrl+C)${NC}"
echo ""
read -r

# ---------------------------------------------------------------------------
# SPEGNIMENTO
# ---------------------------------------------------------------------------
echo ""
echo -e "${YELLOW}[*] Arresto di PostgreSQL...${NC}"
if [ "$OS_TYPE" = "macos" ] && command -v brew &>/dev/null && [ -n "$PG_SERVICE" ]; then
    brew services stop "$PG_SERVICE" &>/dev/null || true
elif [ "$OS_TYPE" = "linux" ]; then
    if command -v systemctl &>/dev/null; then
        sudo systemctl stop postgresql 2>/dev/null || true
    elif command -v service &>/dev/null; then
        sudo service postgresql stop 2>/dev/null || true
    fi
fi
ok "PostgreSQL arrestato. Ciao!"
