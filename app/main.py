
from fastapi import FastAPI

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.customers import router as customers_router
from app.routers.addresses import router as addresses_router
from app.routers.catalog import router as catalog_router
from app.routers.day02 import router as day02_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="ShopSphere Pro E-Commerce Platform API",
)

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(customers_router, prefix=API_PREFIX)
app.include_router(addresses_router, prefix=API_PREFIX)
app.include_router(catalog_router, prefix=API_PREFIX)
app.include_router(day02_router, prefix=API_PREFIX)


@app.get("/", tags=["Health"])
def root():
    return {
        "success": True,
        "message": "ShopSphere Pro API is running",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "success": True,
        "status": "healthy",
    }
