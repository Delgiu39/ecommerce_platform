import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router

# Configurazione del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Avvio dell'applicazione FastAPI...")
    
    # Bootstrap automatico delle tabelle del database su PostgreSQL.
    # Nelle fasi successive useremo Alembic, ma questo assicura che il server
    # parta immediatamente creando le tabelle al primo avvio.
    try:
        async with engine.begin() as conn:
            logger.info("Verifica/Creazione tabelle nel database...")
            # Importa tutti i modelli per assicurarsi che siano registrati su Base.metadata
            from app.models import User, Product, Order, OrderItem, Payment
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Connessione al database riuscita e tabelle pronte.")
    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione del database: {e}")
        raise e
        
    yield
    
    # Pulizia alla chiusura dell'app
    logger.info("Spegnimento dell'applicazione...")
    await engine.dispose()
    logger.info("Connessioni al database chiuse correttamente.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Inclusione dei router dell'applicazione
app.include_router(api_router, prefix=settings.API_V1_STR)


# Configurazione CORS per il collegamento con il frontend React (locale)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],  # 3000 = React CRA, 5173 = React Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": f"Benvenuto nell'API di {settings.PROJECT_NAME}",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME
    }
