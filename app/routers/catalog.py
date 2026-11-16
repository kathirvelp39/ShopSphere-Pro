
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user, require_roles
from app.db.database import get_db
from app.models import (
    Category,
    Brand,
    Product,
    ProductVariant,
    ProductMedia,
)
from app.schemas.catalog import (
    CategoryCreate,
    CategoryUpdate,
    BrandCreate,
    BrandUpdate,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)

router = APIRouter(tags=["Product Catalog"])

ADMIN = ("SUPER_ADMIN", "ADMIN")
PRODUCT_ROLES = ("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER")
MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


# MODULE 6: CATEGORY MANAGEMENT

@router.post("/categories/")
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    if db.query(Category).filter(Category.name == data.name).first():
        raise HTTPException(409, "Category already exists")

    if data.parent_id and not db.query(Category).filter(
        Category.id == data.parent_id
    ).first():
        raise HTTPException(404, "Parent category not found")

    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/categories/")
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.id.desc()).all()


@router.get("/categories/{category_id}")
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")
    return category


@router.patch("/categories/{category_id}")
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    changes = data.model_dump(exclude_unset=True)

    if changes.get("parent_id") == category_id:
        raise HTTPException(400, "A category cannot be its own parent")

    if changes.get("parent_id") and not db.query(Category).filter(
        Category.id == changes["parent_id"]
    ).first():
        raise HTTPException(404, "Parent category not found")

    for key, value in changes.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*ADMIN)),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    if db.query(Product).filter(Product.category_id == category_id).first():
        raise HTTPException(409, "Category has products and cannot be deleted")

    if db.query(Category).filter(Category.parent_id == category_id).first():
        raise HTTPException(409, "Category has subcategories")

    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}


# MODULE 7: BRAND MANAGEMENT

@router.post("/brands/")
def create_brand(
    data: BrandCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    if db.query(Brand).filter(Brand.name == data.name).first():
        raise HTTPException(409, "Brand already exists")

    brand = Brand(**data.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


@router.get("/brands/")
def list_brands(db: Session = Depends(get_db)):
    return db.query(Brand).order_by(Brand.id.desc()).all()


@router.get("/brands/{brand_id}")
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(404, "Brand not found")
    return brand


@router.patch("/brands/{brand_id}")
def update_brand(
    brand_id: int,
    data: BrandUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(404, "Brand not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(brand, key, value)

    db.commit()
    db.refresh(brand)
    return brand


@router.delete("/brands/{brand_id}")
def deactivate_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*ADMIN)),
):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(404, "Brand not found")

    brand.is_active = False
    db.commit()
    return {"message": "Brand deactivated successfully"}


@router.get("/brands/{brand_id}/products")
def products_by_brand(brand_id: int, db: Session = Depends(get_db)):
    if not db.query(Brand).filter(Brand.id == brand_id).first():
        raise HTTPException(404, "Brand not found")

    return db.query(Product).filter(
        Product.brand_id == brand_id,
        Product.is_active.is_(True),
    ).all()


# MODULE 8: PRODUCT MANAGEMENT

@router.post("/products/")
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    if db.query(Product).filter(Product.sku == data.sku).first():
        raise HTTPException(409, "Product SKU already exists")

    if not db.query(Category).filter(
        Category.id == data.category_id,
        Category.is_active.is_(True),
    ).first():
        raise HTTPException(404, "Active category not found")

    if not db.query(Brand).filter(
        Brand.id == data.brand_id,
        Brand.is_active.is_(True),
    ).first():
        raise HTTPException(404, "Active brand not found")

    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products/")
def list_products(
    search: str | None = None,
    category_id: int | None = None,
    brand_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active.is_(True))

    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%")
            | Product.sku.ilike(f"%{search}%")
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    return query.order_by(Product.id.desc()).all()


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active.is_(True),
    ).first()

    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.patch("/products/{product_id}")
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    changes = data.model_dump(exclude_unset=True)

    if changes.get("category_id") and not db.query(Category).filter(
        Category.id == changes["category_id"],
        Category.is_active.is_(True),
    ).first():
        raise HTTPException(404, "Active category not found")

    if changes.get("brand_id") and not db.query(Brand).filter(
        Brand.id == changes["brand_id"],
        Brand.is_active.is_(True),
    ).first():
        raise HTTPException(404, "Active brand not found")

    for key, value in changes.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    product.is_active = False
    db.commit()
    return {"message": "Product deactivated successfully"}


# MODULE 9: PRODUCT VARIANTS

@router.post("/products/{product_id}/variants")
def create_variant(
    product_id: int,
    data: VariantCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    if db.query(ProductVariant).filter(
        ProductVariant.sku == data.sku
    ).first():
        raise HTTPException(409, "Variant SKU already exists")

    variant = ProductVariant(
        product_id=product_id,
        **data.model_dump(),
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


@router.get("/products/{product_id}/variants")
def list_variants(product_id: int, db: Session = Depends(get_db)):
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(404, "Product not found")

    return db.query(ProductVariant).filter(
        ProductVariant.product_id == product_id
    ).all()


@router.patch("/variants/{variant_id}")
def update_variant(
    variant_id: int,
    data: VariantUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id
    ).first()

    if not variant:
        raise HTTPException(404, "Variant not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(variant, key, value)

    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/variants/{variant_id}")
def deactivate_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id
    ).first()

    if not variant:
        raise HTTPException(404, "Variant not found")

    variant.is_active = False
    db.commit()
    return {"message": "Variant deactivated successfully"}


# MODULE 10: PRODUCT IMAGES AND DOCUMENTS

@router.post("/products/{product_id}/media")
async def upload_product_media(
    product_id: int,
    file: UploadFile = File(...),
    variant_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    if variant_id is not None:
        variant = db.query(ProductVariant).filter(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        ).first()
        if not variant:
            raise HTTPException(404, "Variant not found for this product")

    extension = os.path.splitext(file.filename or "")[1].lower()
    expected_type = MEDIA_TYPES.get(extension)

    if not expected_type or file.content_type != expected_type:
        raise HTTPException(400, "Only JPG, PNG, WEBP and PDF files are allowed")

    content = await file.read(settings.MAX_UPLOAD_SIZE + 1)
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(413, "File exceeds the maximum allowed size")

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    stored_name = f"{uuid4().hex}{extension}"
    file_path = os.path.join(upload_dir, stored_name)

    with open(file_path, "wb") as output:
        output.write(content)

    media = ProductMedia(
        product_id=product_id,
        variant_id=variant_id,
        original_filename=os.path.basename(file.filename or "upload"),
        stored_filename=stored_name,
        file_path=file_path,
        content_type=expected_type,
        file_size=len(content),
    )

    db.add(media)
    db.commit()
    db.refresh(media)

    return {
        "message": "File uploaded successfully",
        "media_id": media.id,
        "filename": media.original_filename,
        "content_type": media.content_type,
        "file_size": media.file_size,
    }


@router.get("/products/{product_id}/media")
def list_product_media(product_id: int, db: Session = Depends(get_db)):
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(404, "Product not found")

    return db.query(ProductMedia).filter(
        ProductMedia.product_id == product_id
    ).all()


@router.get("/media/{media_id}/download")
def download_product_media(media_id: int, db: Session = Depends(get_db)):
    media = db.query(ProductMedia).filter(
        ProductMedia.id == media_id
    ).first()

    if not media or not os.path.isfile(media.file_path):
        raise HTTPException(404, "Media file not found")

    return FileResponse(
        media.file_path,
        media_type=media.content_type,
        filename=media.original_filename,
    )


@router.delete("/media/{media_id}")
def delete_product_media(
    media_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(*PRODUCT_ROLES)),
):
    media = db.query(ProductMedia).filter(
        ProductMedia.id == media_id
    ).first()

    if not media:
        raise HTTPException(404, "Media not found")

    if os.path.isfile(media.file_path):
        os.remove(media.file_path)

    db.delete(media)
    db.commit()
    return {"message": "Media deleted successfully"}
