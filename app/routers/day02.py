from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.db.database import get_db
from app.models import Product, ProductVariant
from app.models.day02 import (
    ProductAttribute, ProductAttributeValue, ProductPriceHistory, Warehouse,
    Inventory, InventoryMovement, StockTransfer, StockTransferItem,
    ShoppingCart, CartItem, Wishlist, WishlistItem, Coupon,
)
from app.schemas.day02 import (
    AttributeCreate, AttributeValueCreate, PriceUpdate, WarehouseCreate,
    InventoryCreate, InventoryAdjustment, ThresholdUpdate, TransferCreate,
    CartItemCreate, CartItemUpdate, CouponCreate, CouponValidate,
)

router = APIRouter(tags=["Day 02 - Modules 11 to 20"])
PRODUCT_ROLES = ("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER")
INVENTORY_ROLES = ("SUPER_ADMIN", "ADMIN", "INVENTORY_MANAGER")
ADMIN_ROLES = ("SUPER_ADMIN", "ADMIN")


def _product_or_404(db, product_id):
    product = db.query(Product).filter(Product.id == product_id, Product.is_active.is_(True)).first()
    if not product:
        raise HTTPException(404, "Active product not found")
    return product


def _variant_check(db, product_id, variant_id):
    if variant_id is None:
        return
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.product_id == product_id,
        ProductVariant.is_active.is_(True),
    ).first()
    if not variant:
        raise HTTPException(404, "Active variant not found for this product")


def _get_inventory(db, product_id, variant_id, warehouse_id):
    q = db.query(Inventory).filter(
        Inventory.product_id == product_id,
        Inventory.warehouse_id == warehouse_id,
    )
    if variant_id is None:
        q = q.filter(Inventory.variant_id.is_(None))
    else:
        q = q.filter(Inventory.variant_id == variant_id)
    return q.with_for_update().first()


def _cart_for_user(db, user_id):
    cart = db.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).first()
    if not cart:
        cart = ShoppingCart(user_id=user_id)
        db.add(cart)
        db.flush()
    return cart


def _wishlist_for_user(db, user_id):
    wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.add(wishlist)
        db.flush()
    return wishlist


def _available_stock(db, product_id, variant_id):
    q = db.query(Inventory).join(Warehouse, Warehouse.id == Inventory.warehouse_id).filter(
        Inventory.product_id == product_id,
        Warehouse.is_active.is_(True),
    )
    q = q.filter(Inventory.variant_id.is_(None) if variant_id is None else Inventory.variant_id == variant_id)
    rows = q.all()
    if not rows:
        raise HTTPException(409, "Inventory is not configured for this product/variant")
    return sum(max(0, row.quantity - row.reserved_quantity) for row in rows)


# MODULE 11 - PRODUCT ATTRIBUTES
@router.post("/attributes", status_code=201)
def create_attribute(data: AttributeCreate, db: Session = Depends(get_db),
                     user=Depends(require_roles(*PRODUCT_ROLES))):
    name = data.name.strip()
    if db.query(ProductAttribute).filter(ProductAttribute.name == name).first():
        raise HTTPException(409, "Attribute already exists")
    obj = ProductAttribute(name=name, data_type=data.data_type)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/attributes")
def list_attributes(db: Session = Depends(get_db)):
    return db.query(ProductAttribute).filter(ProductAttribute.is_active.is_(True)).order_by(ProductAttribute.name).all()


@router.post("/products/{product_id}/attributes", status_code=201)
def set_product_attribute(product_id: int, data: AttributeValueCreate,
                          db: Session = Depends(get_db), user=Depends(require_roles(*PRODUCT_ROLES))):
    _product_or_404(db, product_id)
    attr = db.query(ProductAttribute).filter(ProductAttribute.id == data.attribute_id,
                                              ProductAttribute.is_active.is_(True)).first()
    if not attr:
        raise HTTPException(404, "Active attribute not found")
    value = data.value.strip()
    if attr.data_type == "NUMBER":
        try: Decimal(value)
        except Exception: raise HTTPException(422, "Attribute value must be numeric")
    if attr.data_type == "BOOLEAN" and value.lower() not in {"true", "false"}:
        raise HTTPException(422, "Attribute value must be true or false")
    obj = db.query(ProductAttributeValue).filter_by(product_id=product_id, attribute_id=attr.id).first()
    if obj:
        obj.value = value
    else:
        obj = ProductAttributeValue(product_id=product_id, attribute_id=attr.id, value=value)
        db.add(obj)
    db.commit(); db.refresh(obj)
    return obj


@router.get("/products/{product_id}/attributes")
def get_product_attributes(product_id: int, db: Session = Depends(get_db)):
    _product_or_404(db, product_id)
    rows = db.query(ProductAttributeValue, ProductAttribute).join(
        ProductAttribute, ProductAttribute.id == ProductAttributeValue.attribute_id
    ).filter(ProductAttributeValue.product_id == product_id).all()
    return [{"attribute_id": a.id, "name": a.name, "data_type": a.data_type, "value": v.value}
            for v, a in rows]


@router.delete("/products/{product_id}/attributes/{attribute_id}")
def delete_product_attribute_value(product_id: int, attribute_id: int, db: Session = Depends(get_db),
                                   user=Depends(require_roles(*PRODUCT_ROLES))):
    obj = db.query(ProductAttributeValue).filter_by(product_id=product_id, attribute_id=attribute_id).first()
    if not obj: raise HTTPException(404, "Product attribute value not found")
    db.delete(obj); db.commit()
    return {"message": "Product attribute removed"}


# MODULE 12 - PRODUCT PRICING
@router.patch("/products/{product_id}/price")
def update_product_price(product_id: int, data: PriceUpdate, db: Session = Depends(get_db),
                          user=Depends(require_roles(*PRODUCT_ROLES))):
    product = _product_or_404(db, product_id)
    old = Decimal(product.price)
    new = data.price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if old == new: raise HTTPException(400, "New price is same as current price")
    history = ProductPriceHistory(product_id=product.id, old_price=old, new_price=new,
                                  reason=data.reason, changed_by=user.id)
    product.price = new
    db.add(history); db.commit(); db.refresh(product)
    return {"message": "Product price updated", "product_id": product.id,
            "old_price": old, "new_price": new}


@router.get("/products/{product_id}/price-history")
def product_price_history(product_id: int, db: Session = Depends(get_db)):
    _product_or_404(db, product_id)
    return db.query(ProductPriceHistory).filter_by(product_id=product_id).order_by(
        ProductPriceHistory.changed_at.desc()).all()


# MODULE 13 - INVENTORY
@router.post("/inventory", status_code=201)
def create_inventory(data: InventoryCreate, db: Session = Depends(get_db),
                     user=Depends(require_roles(*INVENTORY_ROLES))):
    _product_or_404(db, data.product_id); _variant_check(db, data.product_id, data.variant_id)
    warehouse = db.query(Warehouse).filter(Warehouse.id == data.warehouse_id,
                                            Warehouse.is_active.is_(True)).first()
    if not warehouse: raise HTTPException(404, "Active warehouse not found")
    if _get_inventory(db, data.product_id, data.variant_id, data.warehouse_id):
        raise HTTPException(409, "Inventory record already exists for this product/variant and warehouse")
    obj = Inventory(**data.model_dump())
    db.add(obj); db.flush()
    if data.quantity:
        db.add(InventoryMovement(inventory_id=obj.id, movement_type="OPENING", quantity=data.quantity,
                                 performed_by=user.id, notes="Opening stock"))
    db.commit(); db.refresh(obj)
    return obj


@router.get("/inventory")
def list_inventory(product_id: int | None = None, warehouse_id: int | None = None,
                   db: Session = Depends(get_db), user=Depends(require_roles(*INVENTORY_ROLES))):
    q = db.query(Inventory)
    if product_id is not None: q = q.filter(Inventory.product_id == product_id)
    if warehouse_id is not None: q = q.filter(Inventory.warehouse_id == warehouse_id)
    return q.order_by(Inventory.id.desc()).all()


@router.post("/inventory/{inventory_id}/adjust")
def adjust_inventory(inventory_id: int, data: InventoryAdjustment, db: Session = Depends(get_db),
                     user=Depends(require_roles(*INVENTORY_ROLES))):
    obj = db.query(Inventory).filter(Inventory.id == inventory_id).with_for_update().first()
    if not obj: raise HTTPException(404, "Inventory record not found")
    new_qty = obj.quantity + data.quantity_change
    if new_qty < obj.reserved_quantity:
        raise HTTPException(409, "Cannot reduce stock below reserved quantity")
    if new_qty < 0: raise HTTPException(409, "Insufficient stock")
    if data.quantity_change == 0: raise HTTPException(400, "Quantity change cannot be zero")
    obj.quantity = new_qty
    db.add(InventoryMovement(inventory_id=obj.id, movement_type="ADJUSTMENT",
                             quantity=data.quantity_change, performed_by=user.id, notes=data.notes))
    db.commit(); db.refresh(obj)
    return obj


@router.get("/inventory/{inventory_id}/movements")
def inventory_movements(inventory_id: int, db: Session = Depends(get_db),
                         user=Depends(require_roles(*INVENTORY_ROLES))):
    if not db.query(Inventory).filter(Inventory.id == inventory_id).first():
        raise HTTPException(404, "Inventory record not found")
    return db.query(InventoryMovement).filter_by(inventory_id=inventory_id).order_by(
        InventoryMovement.created_at.desc()).all()


# MODULE 14 - WAREHOUSE
@router.post("/warehouses", status_code=201)
def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db),
                     user=Depends(require_roles(*INVENTORY_ROLES))):
    if db.query(Warehouse).filter((Warehouse.name == data.name) | (Warehouse.code == data.code)).first():
        raise HTTPException(409, "Warehouse name or code already exists")
    obj = Warehouse(**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/warehouses")
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).order_by(Warehouse.name).all()


@router.patch("/warehouses/{warehouse_id}/status")
def set_warehouse_status(warehouse_id: int, is_active: bool, db: Session = Depends(get_db),
                         user=Depends(require_roles(*INVENTORY_ROLES))):
    obj = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not obj: raise HTTPException(404, "Warehouse not found")
    obj.is_active = is_active; db.commit(); db.refresh(obj)
    return obj


@router.get("/warehouses/{warehouse_id}/inventory")
def warehouse_inventory(warehouse_id: int, db: Session = Depends(get_db),
                        user=Depends(require_roles(*INVENTORY_ROLES))):
    if not db.query(Warehouse).filter(Warehouse.id == warehouse_id).first():
        raise HTTPException(404, "Warehouse not found")
    return db.query(Inventory).filter_by(warehouse_id=warehouse_id).all()


# MODULE 15 - INVENTORY TRANSFERS
@router.post("/inventory-transfers", status_code=201)
def request_transfer(data: TransferCreate, db: Session = Depends(get_db),
                     user=Depends(require_roles(*INVENTORY_ROLES))):
    for wid in (data.source_warehouse_id, data.destination_warehouse_id):
        if not db.query(Warehouse).filter(Warehouse.id == wid, Warehouse.is_active.is_(True)).first():
            raise HTTPException(404, f"Active warehouse {wid} not found")
    # Reserve the requested stock immediately so it cannot be allocated twice.
    for item in data.items:
        _product_or_404(db, item.product_id); _variant_check(db, item.product_id, item.variant_id)
        inv = _get_inventory(db, item.product_id, item.variant_id, data.source_warehouse_id)
        if not inv or inv.quantity - inv.reserved_quantity < item.quantity:
            raise HTTPException(409, f"Insufficient available stock for product {item.product_id}")
    transfer = StockTransfer(source_warehouse_id=data.source_warehouse_id,
                             destination_warehouse_id=data.destination_warehouse_id,
                             notes=data.notes, requested_by=user.id)
    db.add(transfer); db.flush()
    for item in data.items:
        inv = _get_inventory(db, item.product_id, item.variant_id, data.source_warehouse_id)
        inv.reserved_quantity += item.quantity
        db.add(StockTransferItem(transfer_id=transfer.id, **item.model_dump()))
    db.commit(); db.refresh(transfer)
    return {"transfer_id": transfer.id, "status": transfer.status, "message": "Stock transfer requested"}


@router.post("/inventory-transfers/{transfer_id}/dispatch")
def dispatch_transfer(transfer_id: int, db: Session = Depends(get_db),
                      user=Depends(require_roles(*INVENTORY_ROLES))):
    transfer = db.query(StockTransfer).filter(StockTransfer.id == transfer_id).with_for_update().first()
    if not transfer: raise HTTPException(404, "Transfer not found")
    if transfer.status != "REQUESTED": raise HTTPException(409, "Only REQUESTED transfers can be dispatched")
    items = db.query(StockTransferItem).filter_by(transfer_id=transfer.id).all()
    for item in items:
        inv = _get_inventory(db, item.product_id, item.variant_id, transfer.source_warehouse_id)
        if not inv or inv.reserved_quantity < item.quantity or inv.quantity < item.quantity:
            raise HTTPException(409, "Reserved source stock is no longer available")
    for item in items:
        inv = _get_inventory(db, item.product_id, item.variant_id, transfer.source_warehouse_id)
        inv.quantity -= item.quantity; inv.reserved_quantity -= item.quantity
        db.add(InventoryMovement(inventory_id=inv.id, movement_type="TRANSFER_OUT",
                                 quantity=-item.quantity, reference=f"TRANSFER-{transfer.id}", performed_by=user.id))
    transfer.status = "DISPATCHED"; transfer.dispatched_at = datetime.utcnow()
    db.commit()
    return {"message": "Transfer dispatched", "transfer_id": transfer.id, "status": transfer.status}


@router.post("/inventory-transfers/{transfer_id}/receive")
def receive_transfer(transfer_id: int, db: Session = Depends(get_db),
                     user=Depends(require_roles(*INVENTORY_ROLES))):
    transfer = db.query(StockTransfer).filter(StockTransfer.id == transfer_id).with_for_update().first()
    if not transfer: raise HTTPException(404, "Transfer not found")
    if transfer.status != "DISPATCHED": raise HTTPException(409, "Only DISPATCHED transfers can be received")
    for item in db.query(StockTransferItem).filter_by(transfer_id=transfer.id).all():
        inv = _get_inventory(db, item.product_id, item.variant_id, transfer.destination_warehouse_id)
        if not inv:
            inv = Inventory(product_id=item.product_id, variant_id=item.variant_id,
                            warehouse_id=transfer.destination_warehouse_id, quantity=0)
            db.add(inv); db.flush()
        inv.quantity += item.quantity
        db.add(InventoryMovement(inventory_id=inv.id, movement_type="TRANSFER_IN",
                                 quantity=item.quantity, reference=f"TRANSFER-{transfer.id}", performed_by=user.id))
    transfer.status = "RECEIVED"; transfer.received_at = datetime.utcnow()
    db.commit()
    return {"message": "Transfer received", "transfer_id": transfer.id, "status": transfer.status}


@router.get("/inventory-transfers/{transfer_id}")
def get_transfer(transfer_id: int, db: Session = Depends(get_db),
                 user=Depends(require_roles(*INVENTORY_ROLES))):
    transfer = db.query(StockTransfer).filter_by(id=transfer_id).first()
    if not transfer: raise HTTPException(404, "Transfer not found")
    items = db.query(StockTransferItem).filter_by(transfer_id=transfer_id).all()
    return {"transfer": transfer, "items": items}


# MODULE 16 - LOW STOCK
@router.patch("/inventory/{inventory_id}/low-stock-threshold")
def update_low_stock_threshold(inventory_id: int, data: ThresholdUpdate, db: Session = Depends(get_db),
                               user=Depends(require_roles(*INVENTORY_ROLES))):
    obj = db.query(Inventory).filter_by(id=inventory_id).first()
    if not obj: raise HTTPException(404, "Inventory record not found")
    obj.low_stock_threshold = data.low_stock_threshold; db.commit(); db.refresh(obj)
    return obj


@router.get("/inventory/low-stock")
def low_stock_report(db: Session = Depends(get_db),
                     user=Depends(require_roles(*INVENTORY_ROLES))):
    rows = db.query(Inventory).filter(
        (Inventory.quantity - Inventory.reserved_quantity) <= Inventory.low_stock_threshold
    ).order_by(Inventory.quantity.asc()).all()
    return [{"inventory_id": x.id, "product_id": x.product_id, "variant_id": x.variant_id,
             "warehouse_id": x.warehouse_id, "quantity": x.quantity,
             "reserved_quantity": x.reserved_quantity,
             "available_quantity": x.quantity - x.reserved_quantity,
             "threshold": x.low_stock_threshold} for x in rows]


# MODULE 17 - SHOPPING CART
@router.post("/cart/items", status_code=201)
def add_cart_item(data: CartItemCreate, db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    product = _product_or_404(db, data.product_id); _variant_check(db, data.product_id, data.variant_id)
    cart = _cart_for_user(db, user.id)
    q = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == data.product_id)
    q = q.filter(CartItem.variant_id.is_(None) if data.variant_id is None else CartItem.variant_id == data.variant_id)
    item = q.first()
    requested_total = (item.quantity if item else 0) + data.quantity
    if requested_total > _available_stock(db, data.product_id, data.variant_id):
        raise HTTPException(409, "Requested quantity exceeds available stock")
    if item: item.quantity = requested_total
    else:
        item = CartItem(cart_id=cart.id, **data.model_dump()); db.add(item)
    db.commit(); db.refresh(item)
    return {"message": "Cart updated", "item_id": item.id, "quantity": item.quantity}


@router.get("/cart")
def get_cart(db: Session = Depends(get_db), user=Depends(get_current_user)):
    cart = _cart_for_user(db, user.id); db.flush()
    rows = db.query(CartItem, Product, ProductVariant).join(
        Product, Product.id == CartItem.product_id
    ).outerjoin(ProductVariant, ProductVariant.id == CartItem.variant_id).filter(
        CartItem.cart_id == cart.id
    ).all()
    items = []
    subtotal = Decimal("0.00")
    for item, product, variant in rows:
        unit = Decimal(variant.price if variant and variant.price is not None else product.price)
        line = unit * item.quantity; subtotal += line
        items.append({"item_id": item.id, "product_id": product.id, "product_name": product.name,
                      "variant_id": variant.id if variant else None, "quantity": item.quantity,
                      "unit_price": unit, "line_total": line})
    return {"cart_id": cart.id, "items": items, "subtotal": subtotal, "item_count": len(items)}


@router.patch("/cart/items/{item_id}")
def update_cart_item(item_id: int, data: CartItemUpdate, db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    cart = _cart_for_user(db, user.id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item: raise HTTPException(404, "Cart item not found")
    if data.quantity > _available_stock(db, item.product_id, item.variant_id):
        raise HTTPException(409, "Requested quantity exceeds available stock")
    item.quantity = data.quantity; db.commit(); db.refresh(item)
    return item


@router.delete("/cart/items/{item_id}")
def remove_cart_item(item_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    cart = _cart_for_user(db, user.id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item: raise HTTPException(404, "Cart item not found")
    db.delete(item); db.commit()
    return {"message": "Cart item removed"}


@router.delete("/cart")
def clear_cart(db: Session = Depends(get_db), user=Depends(get_current_user)):
    cart = _cart_for_user(db, user.id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return {"message": "Cart cleared"}


# MODULE 18 - CART PRICE CALCULATION
@router.post("/cart/price-summary")
def cart_price_summary(coupon_code: str | None = None, shipping_charge: Decimal = Decimal("0.00"),
                       tax_rate: Decimal = Decimal("0.00"), db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    if shipping_charge < 0 or tax_rate < 0 or tax_rate > 100:
        raise HTTPException(422, "Shipping must be >= 0 and tax rate must be between 0 and 100")
    cart = _cart_for_user(db, user.id)
    rows = db.query(CartItem, Product, ProductVariant).join(
        Product, Product.id == CartItem.product_id
    ).outerjoin(ProductVariant, ProductVariant.id == CartItem.variant_id).filter(
        CartItem.cart_id == cart.id
    ).all()
    if not rows: raise HTTPException(400, "Cart is empty")
    subtotal = Decimal("0.00")
    for item, product, variant in rows:
        if not product.is_active: raise HTTPException(409, f"Product {product.id} is inactive")
        if item.quantity > _available_stock(db, product.id, item.variant_id):
            raise HTTPException(409, f"Insufficient available stock for product {product.id}")
        unit = Decimal(variant.price if variant and variant.price is not None else product.price)
        if variant and not variant.is_active: raise HTTPException(409, "Cart contains an inactive variant")
        subtotal += unit * item.quantity
    discount = Decimal("0.00")
    if coupon_code:
        coupon = db.query(Coupon).filter(Coupon.code == coupon_code.upper()).first()
        now = datetime.utcnow()
        if not coupon or not coupon.is_active or now < coupon.starts_at or now > coupon.expires_at:
            raise HTTPException(400, "Coupon is invalid or outside its validity period")
        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            raise HTTPException(400, "Coupon usage limit reached")
        if subtotal < coupon.minimum_purchase: raise HTTPException(400, "Minimum purchase amount not met")
        if coupon.discount_type == "PERCENT": discount = subtotal * coupon.discount_value / Decimal("100")
        else: discount = coupon.discount_value
        discount = min(discount, subtotal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    taxable = subtotal - discount
    tax = (taxable * tax_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = taxable + tax + shipping_charge
    return {"subtotal": subtotal, "discount": discount, "tax_rate_percent": tax_rate,
            "tax_amount": tax, "shipping_charge": shipping_charge, "total": total}


# MODULE 19 - WISHLIST
@router.post("/wishlist/{product_id}", status_code=201)
def add_wishlist_item(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _product_or_404(db, product_id)
    wishlist = _wishlist_for_user(db, user.id)
    item = db.query(WishlistItem).filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
    if item: raise HTTPException(409, "Product already exists in wishlist")
    item = WishlistItem(wishlist_id=wishlist.id, product_id=product_id)
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.get("/wishlist")
def get_wishlist(db: Session = Depends(get_db), user=Depends(get_current_user)):
    wishlist = _wishlist_for_user(db, user.id); db.flush()
    return db.query(WishlistItem, Product).join(Product, Product.id == WishlistItem.product_id).filter(
        WishlistItem.wishlist_id == wishlist.id
    ).all()


@router.delete("/wishlist/{product_id}")
def remove_wishlist_item(product_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    wishlist = _wishlist_for_user(db, user.id)
    item = db.query(WishlistItem).filter_by(wishlist_id=wishlist.id, product_id=product_id).first()
    if not item: raise HTTPException(404, "Wishlist item not found")
    db.delete(item); db.commit()
    return {"message": "Product removed from wishlist"}


# MODULE 20 - COUPONS
@router.post("/coupons", status_code=201)
def create_coupon(data: CouponCreate, db: Session = Depends(get_db),
                  user=Depends(require_roles(*PRODUCT_ROLES))):
    code = data.code.strip().upper()
    if db.query(Coupon).filter(Coupon.code == code).first(): raise HTTPException(409, "Coupon code already exists")
    obj = Coupon(**data.model_dump(exclude={"code"}), code=code, created_by=user.id)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/coupons")
def list_coupons(db: Session = Depends(get_db), user=Depends(require_roles(*PRODUCT_ROLES))):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


@router.patch("/coupons/{coupon_id}/status")
def set_coupon_status(coupon_id: int, is_active: bool, db: Session = Depends(get_db),
                      user=Depends(require_roles(*PRODUCT_ROLES))):
    obj = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not obj: raise HTTPException(404, "Coupon not found")
    obj.is_active = is_active; db.commit(); db.refresh(obj)
    return obj


@router.post("/coupons/validate")
def validate_coupon(data: CouponValidate, db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter(Coupon.code == data.code.strip().upper()).first()
    now = datetime.utcnow()
    if not coupon or not coupon.is_active or now < coupon.starts_at or now > coupon.expires_at:
        raise HTTPException(400, "Coupon is invalid or expired")
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise HTTPException(400, "Coupon usage limit reached")
    if data.subtotal < coupon.minimum_purchase: raise HTTPException(400, "Minimum purchase amount not met")
    discount = data.subtotal * coupon.discount_value / Decimal("100") if coupon.discount_type == "PERCENT" else coupon.discount_value
    discount = min(discount, data.subtotal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"valid": True, "coupon_code": coupon.code, "discount_amount": discount,
            "payable_subtotal": data.subtotal - discount}
