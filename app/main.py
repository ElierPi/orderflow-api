import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routes.products import router as products_router
from app.routes import auth, customers, dashboard, inventory, orders


app = FastAPI(
    title="OrderFlow API",
    description="Backend API for order and inventory management",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if value.strip()],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(_request, exc):
    # Never echo submitted passwords or other raw input in validation responses.
    return JSONResponse(status_code=422, content={
        "detail": [{key: error[key] for key in ("type", "loc", "msg")} for error in exc.errors()]
    })


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
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
