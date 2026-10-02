from fastapi import FastAPI

from app.routes.products import router as products_router


app = FastAPI(
    title="OrderFlow API",
    description="Backend API for order and inventory management",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "OrderFlow API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


app.include_router(products_router)