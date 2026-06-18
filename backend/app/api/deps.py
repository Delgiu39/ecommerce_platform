from app.core.database import get_db

# Qui in seguito definiremo altre dipendenze come get_current_user (JWT auth)
__all__ = ["get_db"]
