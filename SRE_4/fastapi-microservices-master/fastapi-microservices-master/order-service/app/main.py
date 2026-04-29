import os
from datetime import datetime, timezone
from decimal import Decimal

import requests
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/microservices_db")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
security = HTTPBearer()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    total = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    items = relationship("OrderItem", cascade="all, delete-orphan", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    order = relationship("Order", back_populates="items")


class OrderItemPayload(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderPayload(BaseModel):
    items: list[OrderItemPayload]


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total: Decimal
    items: list[OrderItemResponse]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def fetch_product(product_id: int) -> dict:
    try:
        response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Product service unavailable")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Product service error")
    return response.json()


def order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total=order.total,
        items=[
            OrderItemResponse(product_id=item.product_id, quantity=item.quantity, unit_price=item.unit_price)
            for item in order.items
        ],
    )


app = FastAPI(title="Order Service", openapi_url="/orders/openapi.json", docs_url="/orders/docs")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/orders/health")
def health():
    return {"status": "ok", "service": "order-service"}


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderPayload, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    order = Order(user_id=user_id, total=Decimal("0.00"))
    db.add(order)
    total = Decimal("0.00")

    for item_payload in payload.items:
        product = fetch_product(item_payload.product_id)
        if product["stock"] < item_payload.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for product {product['id']}")
        unit_price = Decimal(str(product["price"]))
        total += unit_price * item_payload.quantity
        order.items.append(
            OrderItem(product_id=product["id"], quantity=item_payload.quantity, unit_price=unit_price)
        )

    order.total = total
    db.commit()
    db.refresh(order)
    return order_response(order)


@app.get("/orders", response_model=list[OrderResponse])
def list_my_orders(user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.id.desc()).all()
    return [order_response(order) for order in orders]
