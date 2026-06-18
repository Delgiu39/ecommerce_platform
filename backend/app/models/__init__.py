from app.core.database import Base
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.payment import Payment

# Esponiamo tutti i modelli per consentire ad Alembic o a SQLAlchemy
# di scansionare i metadati da un unico punto di ingresso.
__all__ = ["Base", "User", "Product", "Order", "OrderItem", "Payment"]
