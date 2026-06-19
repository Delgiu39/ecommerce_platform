# E-Commerce Platform con Gateway di Pagamento Stripe

Una piattaforma e-commerce **full-stack** moderna, sicura e pronta per la produzione, realizzata con **FastAPI** (backend) e **React + Vite** (frontend). Integra il gateway di pagamento **Stripe** con supporto nativo a una modalità di simulazione locale (Mock Mode) per lo sviluppo senza chiavi reali.

---

## Indice

- [Panoramica del Progetto](#panoramica-del-progetto)
- [Stack Tecnologico](#stack-tecnologico)
- [Architettura del Sistema](#architettura-del-sistema)
- [Struttura del Repository](#struttura-del-repository)
- [Funzionalita Principali](#funzionalita-principali)
- [Prerequisiti](#prerequisiti)
- [Configurazione e Avvio](#configurazione-e-avvio)
  - [1. Avvio del Database PostgreSQL](#1-avvio-del-database-postgresql)
  - [2. Avvio del Backend FastAPI](#2-avvio-del-backend-fastapi)
  - [3. Avvio del Frontend React](#3-avvio-del-frontend-react)
- [Variabili d'Ambiente](#variabili-dambiente)
- [Documentazione API](#documentazione-api)
- [Flusso di Pagamento](#flusso-di-pagamento)
- [Suite di Test](#suite-di-test)
- [Sicurezza](#sicurezza)

---

## Panoramica del Progetto

Questo progetto nasce come dimostrazione pratica di un sistema e-commerce completo con gateway di pagamento integrato. L'obiettivo e costruire un'applicazione reale, non un semplice prototipo, con:

- autenticazione stateless tramite **JWT**
- gestione dello **stock a magazzino** in tempo reale
- **checkout sicuro** con Stripe Elements (iframe PCI-DSS compliant)
- **simulazione locale** del webhook Stripe per lo sviluppo offline
- **test automatizzati** per tutti i flussi critici
- un'interfaccia utente **dark/glassmorphism** premium

---

## Stack Tecnologico

### Backend
| Tecnologia | Versione | Ruolo |
|---|---|---|
| Python | 3.11+ | Linguaggio principale |
| FastAPI | >= 0.110 | Framework API REST asincrono |
| SQLAlchemy | >= 2.0 | ORM asincrono (asyncpg) |
| PostgreSQL | 16 | Database relazionale |
| Alembic | >= 1.13 | Migrazioni dello schema DB |
| Pydantic v2 | >= 2.6 | Validazione dati e serializzazione |
| PyJWT | >= 2.8 | Generazione e verifica token JWT |
| bcrypt | >= 4.1 | Hashing sicuro delle password |
| Stripe SDK | >= 8.5 | Integrazione gateway di pagamento |
| Uvicorn | >= 0.28 | Server ASGI ad alte prestazioni |

### Frontend
| Tecnologia | Versione | Ruolo |
|---|---|---|
| React | 19 | Libreria UI component-based |
| Vite | 8 | Build tool e dev server ultra-veloce |
| @stripe/react-stripe-js | 6 | Componenti React per Stripe Elements |
| @stripe/stripe-js | 9 | SDK Stripe lato client |
| lucide-react | 1.x | Set di icone SVG moderne |
| Vanilla CSS | — | Styling con variabili CSS e glassmorphism |

### Test
| Tecnologia | Versione | Ruolo |
|---|---|---|
| pytest | >= 8.0 | Framework di test |
| pytest-asyncio | >= 0.23 | Supporto test asincroni |
| httpx | >= 0.27 | Client HTTP per i test di integrazione |

---

## Architettura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                     Browser                         │
│              React + Vite SPA                       │
│         http://localhost:5173                       │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/JSON (REST API)
                     ▼
┌─────────────────────────────────────────────────────┐
│                 FastAPI Backend                     │
│            http://127.0.0.1:8000                   │
│                                                     │
│  /api/v1/auth      → Autenticazione JWT            │
│  /api/v1/products  → Catalogo prodotti             │
│  /api/v1/orders    → Gestione ordini               │
│  /api/v1/payments  → Gateway Stripe                │
└────────────┬──────────────────┬────────────────────┘
             │                  │
             ▼                  ▼
┌────────────────────┐  ┌──────────────────┐
│   PostgreSQL DB    │  │   Stripe API     │
│   porta 5432       │  │  (se configurato)│
└────────────────────┘  └──────────────────┘
```

---

## Struttura del Repository

```
ecommerce_platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py              # Dipendenze FastAPI (auth, db)
│   │   │   └── v1/
│   │   │       ├── api.py           # Router principale v1
│   │   │       └── endpoints/
│   │   │           ├── auth.py      # Login, registrazione, /me
│   │   │           ├── products.py  # CRUD prodotti
│   │   │           ├── orders.py    # Creazione e lettura ordini
│   │   │           └── payments.py  # Stripe intent, webhook
│   │   ├── core/
│   │   │   ├── config.py            # Configurazione da .env
│   │   │   ├── database.py          # Connessione asincrona DB
│   │   │   └── security.py          # JWT, password hashing
│   │   ├── models/                  # Modelli SQLAlchemy
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── order.py
│   │   │   └── payment.py
│   │   ├── repositories/            # Layer di accesso al DB
│   │   ├── schemas/                 # Schemi Pydantic (I/O)
│   │   └── main.py                  # Entry point FastAPI
│   ├── alembic/                     # Migrazioni schema DB
│   ├── tests/                       # Suite pytest
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_products.py
│   │   ├── test_orders.py
│   │   └── test_payments.py
│   ├── postgresql/                  # PostgreSQL portatile (Windows)
│   ├── .env                         # Variabili d'ambiente (non tracciato)
│   ├── .env.example                 # Template variabili d'ambiente
│   ├── requirements.txt
│   ├── start_postgres.bat           # Script avvio PostgreSQL (Windows)
│   └── stop_postgres.bat            # Script arresto PostgreSQL (Windows)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx           # Barra di navigazione glassmorphism
│   │   │   ├── ProductList.jsx      # Griglia catalogo prodotti
│   │   │   ├── Cart.jsx             # Carrello + step di checkout
│   │   │   ├── CheckoutForm.jsx     # Stripe Elements / Mock form
│   │   │   ├── Orders.jsx           # Storico ordini
│   │   │   ├── Login.jsx            # Form di accesso
│   │   │   └── Register.jsx         # Form di registrazione
│   │   ├── context/
│   │   │   ├── AuthContext.jsx      # Stato globale autenticazione
│   │   │   └── CartContext.jsx      # Stato globale carrello
│   │   ├── App.jsx                  # Root component e routing
│   │   ├── main.jsx                 # Entry point React
│   │   └── index.css                # Design system e variabili CSS
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## Funzionalita Principali

### Autenticazione e Autorizzazione
- Registrazione con validazione email e password (minimo 6 caratteri)
- Login con rilascio di **JWT Bearer Token** (scadenza configurabile)
- Endpoint protetti tramite dependency injection FastAPI
- Ruolo **superuser** per operazioni amministrative (gestione prodotti, simulazione webhook)
- Blocco del privilege escalation: il campo `is_superuser` e ignorato in fase di registrazione

### Catalogo Prodotti
- Lettura pubblica del catalogo senza autenticazione
- Creazione, aggiornamento ed eliminazione riservati agli amministratori
- Campi: nome, descrizione, prezzo, stock, URL immagine, stato attivo
- Validazione dei dati in ingresso con Pydantic v2

### Gestione Ordini
- Creazione ordine con verifica disponibilita stock in tempo reale
- Decremento atomico dello stock alla conferma dell'ordine
- Ogni utente puo visualizzare solo i propri ordini
- Gli amministratori hanno visibilita su tutti gli ordini
- Stati dell'ordine: `pending` → `paid` / `failed`

### Gateway di Pagamento
- **Modalita Stripe reale**: crea un `PaymentIntent` tramite le API Stripe, rilascia il `client_secret` al frontend per il rendering di `CardElement` (iframe PCI-DSS sicuro)
- **Modalita Mock locale**: se `STRIPE_SECRET_KEY` e vuoto nel `.env`, genera un `client_secret` fittizio con prefisso `mock_cs_`. Il frontend lo riconosce e mostra un modulo demo. Il completamento avviene tramite l'endpoint `/payments/simulate-webhook`
- Gestione del webhook Stripe con verifica della firma (`STRIPE_WEBHOOK_SECRET`) in produzione
- Ripristino dello stock in caso di pagamento fallito

### Interfaccia Utente
- Design **dark premium** con tema blu notte / viola / ciano elettrico
- Effetto **glassmorphism** su card e navbar (backdrop-filter blur)
- Animazioni hover fluide e micro-animazioni fade-in
- Tipografia moderna con font **Outfit** (Google Fonts)
- Indicatore dinamico del numero di articoli nel carrello
- Doppia modalita di checkout (Stripe Elements / Simulatore Mock)
- Vista "I Miei Ordini" con badge di stato colorati e opzione "Completa Pagamento" per ordini pendenti

---

## Prerequisiti

- **Python** 3.11 o superiore
- **Node.js** 18 o superiore (con npm)
- **PostgreSQL** 14+ (oppure usare il binario portatile incluso in `backend/postgresql/` per Windows)

---

## Configurazione e Avvio

### Metodo Automatico (Consigliato — Windows)

Per avviare l'intera applicazione con un unico comando usa gli script inclusi nella root del progetto.

Questi script eseguono automaticamente:
1. **Verifica dei prerequisiti** — controllano che `python` e `node` siano disponibili nel PATH.
2. **Configurazione Backend** — creano il `venv` Python, installano le dipendenze da `requirements.txt` (con auto-riparazione del venv se corrotto), copiano `.env.example` in `.env` e generano una `SECRET_KEY` crittografica sicura se mancante.
3. **Configurazione Frontend** — eseguono `npm install` se `node_modules` non è presente.
4. **Avvio PostgreSQL** — avviano il database portatile con `pg_ctl -w start` (attende la conferma di avvio prima di proseguire) e creano il database `ecommerce_db` se non esiste.
5. **Avvio Backend e Frontend** — aprono due finestre separate con il server FastAPI (porta 8000) e il dev server Vite (porta 5173).
6. **Apertura automatica del browser** su `http://localhost:5173`.
7. **Spegnimento pulito** — alla pressione di INVIO, arrestano PostgreSQL con `pg_ctl stop` prima di chiudersi.

> [!IMPORTANT]
> Il database PostgreSQL portatile è incluso nella cartella `backend/postgresql/` — non è necessario installare nulla di aggiuntivo.

#### Opzione A — Doppio Clic (CMD Batch)
Fai doppio clic su `start.bat` nella cartella principale del progetto, oppure eseguilo da terminale:
```cmd
.\start.bat
```

#### Opzione B — PowerShell
```powershell
.\start.ps1
```

---

### Metodo Manuale (Dettagliato)

Se preferisci controllare singolarmente ogni servizio o se non sei su Windows:

#### 1. Avvio del Database PostgreSQL

**Opzione A — Binario portatile incluso (Windows)**

Fare doppio clic su `backend/start_postgres.bat` oppure eseguire da PowerShell:

```powershell
cd "ecommerce_platform\backend"
.\start_postgres.bat
```

**Opzione B — PostgreSQL di sistema**

Assicurarsi che PostgreSQL sia in esecuzione e creare il database:

```sql
CREATE DATABASE ecommerce_db;
```

---

#### 2. Avvio del Backend FastAPI

```powershell
cd "ecommerce_platform\backend"

# Creare l'ambiente virtuale (solo la prima volta)
python -m venv venv

# Attivare l'ambiente virtuale
.\venv\Scripts\Activate.ps1

# Installare le dipendenze (solo la prima volta)
pip install -r requirements.txt

# Copiare il template delle variabili d'ambiente
copy .env.example .env
# Modificare .env con i propri valori

# Avviare il server
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> Le migrazioni Alembic vengono eseguite automaticamente all'avvio dell'applicazione (`alembic upgrade head`). Non e necessario eseguirle manualmente.

Il backend sara disponibile su: **http://127.0.0.1:8000**

---

#### 3. Avvio del Frontend React

```powershell
cd "ecommerce_platform\frontend"

# Installare le dipendenze (solo la prima volta)
npm install

# Avviare il server di sviluppo
npm run dev
```

Il frontend sara disponibile su: **http://localhost:5173**

---


## Variabili d'Ambiente

Copiare `backend/.env.example` in `backend/.env` e compilare i valori:

```env
PROJECT_NAME="E-Commerce Payment Platform"
API_V1_STR="/api/v1"

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ecommerce_db
POSTGRES_PORT=5432

# Sicurezza JWT
SECRET_KEY=<stringa-casuale-di-64-caratteri>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe (lasciare vuoti per usare il Mock Mode locale)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

### Generare una SECRET_KEY sicura

```python
import secrets
print(secrets.token_hex(32))
```

### Modalita Stripe

| Configurazione | Comportamento |
|---|---|
| `STRIPE_SECRET_KEY` vuoto | **Mock Mode**: pagamenti simulati localmente, nessuna chiamata a Stripe |
| `STRIPE_SECRET_KEY` impostato | **Stripe reale**: crea PaymentIntent reali, richiede anche `STRIPE_WEBHOOK_SECRET` per i webhook |

---

## Documentazione API

Con il backend in esecuzione, la documentazione interattiva e disponibile a:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Endpoints principali

| Metodo | Endpoint | Auth | Descrizione |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | No | Registrazione nuovo utente |
| `POST` | `/api/v1/auth/login` | No | Login, ritorna JWT token |
| `GET` | `/api/v1/auth/me` | Utente | Profilo utente corrente |
| `GET` | `/api/v1/products/` | No | Lista prodotti del catalogo |
| `POST` | `/api/v1/products/` | Admin | Crea nuovo prodotto |
| `PUT` | `/api/v1/products/{id}` | Admin | Aggiorna prodotto |
| `DELETE` | `/api/v1/products/{id}` | Admin | Elimina prodotto |
| `POST` | `/api/v1/orders/` | Utente | Crea ordine (scala stock) |
| `GET` | `/api/v1/orders/` | Utente | Lista ordini dell'utente |
| `GET` | `/api/v1/orders/{id}` | Utente | Dettagli ordine |
| `POST` | `/api/v1/payments/create-intent/{order_id}` | Utente | Crea PaymentIntent Stripe |
| `POST` | `/api/v1/payments/webhook` | No (firma) | Ricezione eventi Stripe |
| `POST` | `/api/v1/payments/simulate-webhook` | Admin | Simula esito pagamento (dev) |

---

## Flusso di Pagamento

### Modalita Mock (sviluppo locale senza Stripe)

```
Utente                  Frontend               Backend              DB
  |                        |                      |                  |
  |-- Aggiungi al carrello →|                      |                  |
  |-- Procedi al checkout →|                      |                  |
  |                        |-- POST /orders/ ----→|                  |
  |                        |                      |-- Valida stock --→|
  |                        |                      |←-- Ordine creato-|
  |                        |←--- orderId ---------                   |
  |                        |-- POST /create-intent/{id} ----------→  |
  |                        |←--- mock_cs_xxxx (client_secret) -----  |
  |                        |                                         |
  |  [Modulo carta fittizio visibile]                                |
  |-- Clicca "Paga Ora" →|                                          |
  |                        |-- POST /simulate-webhook?event=succeeded|
  |                        |←--- {status: "success"} -------------- |
  |                        |                      |-- Aggiorna DB --→|
  |←-- Schermata successo--|                                         |
```

### Modalita Stripe Reale (produzione)

```
Utente                  Frontend               Backend           Stripe
  |                        |                      |                 |
  |-- Procedi al checkout →|                      |                 |
  |                        |-- POST /create-intent/{id} ----------→|
  |                        |                      |-- PaymentIntent→|
  |                        |                      |←-- client_secret|
  |                        |←--- client_secret ---|                 |
  |                        |                                        |
  |  [Stripe CardElement (iframe) visibile]                        |
  |-- Inserisce carta ----→|                                        |
  |-- Clicca "Paga Ora" →|-- confirmCardPayment() --------------- →|
  |                        |←--- paymentIntent.succeeded ----------|
  |                        |                      |←-- Webhook -----|
  |                        |                      |-- Aggiorna DB  |
  |←-- Schermata successo--|                                        |
```

---

## Suite di Test

La test suite copre tutti i flussi critici dell'applicazione con test asincroni isolati.

```powershell
cd "ecommerce_platform\backend"
.\venv\Scripts\python.exe -m pytest tests/ -v
```

**Risultato atteso:**

```
collected 13 items

tests/test_auth.py::test_register_success PASSED
tests/test_auth.py::test_register_invalid_email PASSED
tests/test_auth.py::test_register_short_password PASSED
tests/test_auth.py::test_register_blocks_superuser_escalation PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_wrong_password PASSED
tests/test_auth.py::test_me_endpoint PASSED
tests/test_orders.py::test_create_order_and_stock_decrement PASSED
tests/test_payments.py::test_create_payment_intent PASSED
tests/test_products.py::test_list_products_public PASSED
tests/test_products.py::test_create_product_admin_only PASSED
tests/test_products.py::test_get_single_product PASSED
tests/test_products.py::test_full_crud_as_admin PASSED

13 passed in ~4.5s
```

### Copertura dei test

| Modulo | Test coperti |
|---|---|
| Autenticazione | Registrazione, validazione, blocco escalation privilegi, login, JWT |
| Prodotti | Lettura pubblica, blocco non-admin, CRUD amministrativo |
| Ordini | Creazione, decremento stock, controllo accessi |
| Pagamenti | Creazione PaymentIntent, simulazione webhook, aggiornamento stato |

---

## Sicurezza

Il progetto implementa le seguenti misure di sicurezza:

| Misura | Implementazione |
|---|---|
| **Hashing password** | bcrypt con salt automatico |
| **Autenticazione stateless** | JWT HS256 con scadenza configurabile |
| **Segreti fuori dal codice** | Tutte le chiavi in `.env` (non tracciato in Git) |
| **Validazione input** | Pydantic v2 con vincoli su tutti i campi |
| **Controllo accessi** | Dependency injection FastAPI per ogni endpoint protetto |
| **Blocco privilege escalation** | `is_superuser` ignorato durante la registrazione |
| **Verifica firma webhook** | `stripe.Webhook.construct_event()` in produzione |
| **CORS** | Configurabile tramite `settings` (da restringere in produzione) |
| **Prevenzione negative stock** | Validazione stock prima della creazione ordine |

> **Nota**: il file `.env` e incluso nel `.gitignore` e non viene mai tracciato nel repository. Usare sempre `.env.example` come riferimento.