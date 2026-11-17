from app.db.database import Base, engine
from app.models import (
    User, TokenSession, CustomerProfile, ProfileHistory,
    Address, Category, Brand, Product, ProductVariant, ProductMedia,
    ProductAttribute, ProductAttributeValue, ProductPriceHistory, Warehouse,
    Inventory, InventoryMovement, StockTransfer, StockTransferItem,
    ShoppingCart, CartItem, Wishlist, WishlistItem, Coupon,
)


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("SHOPSPHERE PRO TABLES CREATED SUCCESSFULLY")


if __name__ == "__main__":
    create_tables()