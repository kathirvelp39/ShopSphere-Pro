
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    role: str | None = None
    is_active: bool | None = None


class CustomerProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone_number: str | None = Field(default=None, max_length=20)


class AddressCreate(BaseModel):
    address_type: str = "SHIPPING"
    full_name: str
    phone_number: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool = False


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: int | None = None


class BrandCreate(BaseModel):
    name: str
    description: str | None = None


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    sku: str
    price: Decimal = Field(gt=0)
    category_id: int
    brand_id: int | None = None


class VariantCreate(BaseModel):
    name: str
    value: str
    sku: str
    price: Decimal | None = Field(default=None, gt=0)
    stock_quantity: int = Field(default=0, ge=0)


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    parent_id: int | None = None
    is_active: bool | None = None


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    is_active: bool | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    category_id: int | None = None
    brand_id: int | None = None
    is_active: bool | None = None


class VariantUpdate(BaseModel):
    name: str | None = None
    value: str | None = None
    price: float | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
