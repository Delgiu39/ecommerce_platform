from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )
    
    PROJECT_NAME: str = "E-Commerce Payment Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ecommerce_db"
    POSTGRES_PORT: int = 5432
    
    DATABASE_URL: Optional[str] = None

    # Security Settings
    SECRET_KEY: str = "92a838df2c5e52c8b74c3e80e18bb3efc023d8c1ee12d591b7d5a5cfcd8198f3"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Stripe Settings
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None


    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            # Assicura che sia usato asyncpg
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def sync_database_url(self) -> str:
        """Usato principalmente per Alembic o driver sincroni"""
        url = self.async_database_url
        return url.replace("postgresql+asyncpg://", "postgresql://")

settings = Settings()
