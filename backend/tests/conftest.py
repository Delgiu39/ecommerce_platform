import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from httpx import AsyncClient, ASGITransport

TEST_DB_NAME = "ecommerce_test_db"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def setup_test_db():
    # Connessione al database di default 'postgres' per creare il db di test
    default_url = settings.async_database_url.replace(settings.POSTGRES_DB, "postgres")
    admin_engine = create_async_engine(default_url, isolation_level="AUTOCOMMIT")
    
    async with admin_engine.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    await admin_engine.dispose()
    
    # Connessione al database di test appena creato e creazione delle tabelle
    test_url = settings.async_database_url.replace(settings.POSTGRES_DB, TEST_DB_NAME)
    test_engine = create_async_engine(test_url)
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield test_engine
    
    # Pulizia alla fine della sessione
    await test_engine.dispose()
    
    admin_engine = create_async_engine(default_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
    await admin_engine.dispose()

@pytest.fixture(autouse=True)
async def clean_db(setup_test_db):
    test_engine = setup_test_db
    yield
    # Svuota tutte le tabelle per isolare i test
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

@pytest.fixture
async def db(setup_test_db):
    test_engine = setup_test_db
    SessionLocal = async_sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with SessionLocal() as session:
        yield session

@pytest.fixture
async def client(setup_test_db):
    test_engine = setup_test_db
    SessionLocal = async_sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    
    async def override_get_db():
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
                
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
