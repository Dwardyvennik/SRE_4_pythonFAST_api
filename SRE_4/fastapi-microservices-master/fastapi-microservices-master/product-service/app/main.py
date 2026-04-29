import os
import time
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, status
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, Numeric, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/microservices_db")
SERVICE_NAME = "product-service"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status", "service_name"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status", "service_name"],
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint", "service_name"],
)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProductPayload(BaseModel):
    name: str
    description: str | None = None
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)


class ProductResponse(ProductPayload):
    id: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def product_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
    )

def seed_products(db: Session):
    if db.query(Product).count() > 0:
        return
    db.add_all(
        [
            Product(name="Laptop", description="Development laptop", price=Decimal("1200.00"), stock=10),
            Product(name="Keyboard", description="Mechanical keyboard", price=Decimal("85.50"), stock=25),
            Product(name="Mouse", description="Wireless mouse", price=Decimal("35.00"), stock=40),
        ]
    )
    db.commit()


app = FastAPI(title="Product Service", openapi_url="/products/openapi.json", docs_url="/products/docs")
Instrumentator().expose(app, endpoint="/metrics", include_in_schema=False)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    endpoint = request.url.path
    if endpoint == "/metrics":
        return await call_next(request)

    method = request.method
    status_code = "500"
    start_time = time.perf_counter()
    in_progress = HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint, service_name=SERVICE_NAME)
    in_progress.inc()
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    finally:
        duration = time.perf_counter() - start_time
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status=status_code,
            service_name=SERVICE_NAME,
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            endpoint=endpoint,
            status=status_code,
            service_name=SERVICE_NAME,
        ).observe(duration)
        in_progress.dec()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_products(db)


@app.get("/products/health")
def health():
    return {"status": "ok", "service": "product-service"}


@app.get("/products", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return [product_response(product) for product in db.query(Product).order_by(Product.id).all()]


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductPayload, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product_response(product)


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_response(product)


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, payload: ProductPayload, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product_response(product)


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product:
        db.delete(product)
        db.commit()
