from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AttributeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    data_type: str = Field(default="TEXT", pattern="^(TEXT|NUMBER|BOOLEAN)$")


class AttributeValueCreate(BaseModel):
    attribute_id: int
    value: str = Field(min_length=1, max_length=255)


class PriceUpdate(BaseModel):
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reason: str | None = Field(default=None, max_length=255)


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=40)
    address: str | None = None
    capacity: int | None = Field(default=None, gt=0)


class InventoryCreate(BaseModel):
    product_id: int
    variant_id: int | None = None
    warehouse_id: int
    quantity: int = Field(ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)


class InventoryAdjustment(BaseModel):
    quantity_change: int
    notes: str | None = None


class ThresholdUpdate(BaseModel):
    low_stock_threshold: int = Field(ge=0)


class TransferItemCreate(BaseModel):
    product_id: int
    variant_id: int | None = None
    quantity: int = Field(gt=0)


class TransferCreate(BaseModel):
    source_warehouse_id: int
    destination_warehouse_id: int
    notes: str | None = None
    items: list[TransferItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_warehouses(self):
        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError("Source and destination warehouses must differ")
        return self


class CartItemCreate(BaseModel):
    product_id: int
    variant_id: int | None = None
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    description: str | None = None
    discount_type: str = Field(pattern="^(PERCENT|FIXED)$")
    discount_value: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    minimum_purchase: Decimal = Field(default=Decimal("0"), ge=0)
    starts_at: datetime
    expires_at: datetime
    usage_limit: int | None = Field(default=None, gt=0)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_coupon(self):
        if self.expires_at <= self.starts_at:
            raise ValueError("expires_at must be later than starts_at")
        if self.discount_type == "PERCENT" and self.discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100")
        return self


class CouponValidate(BaseModel):
    code: str
    subtotal: Decimal = Field(ge=0)
