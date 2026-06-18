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

import os
from fastapi.concurrency import run_in_threadpool
from alembic.config import Config
from alembic import command

def run_migrations():
    """
    Esegue programmaticamente le migrazioni di database con Alembic.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(base_dir, "..", "alembic.ini")
    
    # Istanziamo la configurazione di Alembic puntando al file ini
    alembic_cfg = Config(ini_path)
    
    # Impostiamo la directory dello script in modo assoluto
    alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "..", "alembic"))
    
    logger.info("Avvio upgrade database ad 'head' tramite Alembic...")
    command.upgrade(alembic_cfg, "head")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Avvio dell'applicazione FastAPI...")
    
    # Esecuzione delle migrazioni del database tramite Alembic all'avvio.
    try:
        logger.info("Verifica/Esecuzione migrazioni nel database...")
        await run_in_threadpool(run_migrations)
        logger.info("Connessione al database riuscita e schema allineato.")
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
    allow_origins=settings.BACKEND_CORS_ORIGINS,
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
