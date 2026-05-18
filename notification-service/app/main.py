import os
import time
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Boolean, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/microservices_db")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
SERVICE_NAME = "notification-service"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
security = HTTPBearer()

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


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class NotificationCreate(BaseModel):
    user_id: int
    message: str


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime


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


app = FastAPI(title="Notification Service", openapi_url="/notifications/openapi.json", docs_url="/notifications/docs")
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
            method=method, endpoint=endpoint, status=status_code, service_name=SERVICE_NAME
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method, endpoint=endpoint, status=status_code, service_name=SERVICE_NAME
        ).observe(duration)
        in_progress.dec()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health", include_in_schema=False)
@app.get("/notifications/health")
def health():
    return {"status": "ok", "service": SERVICE_NAME}


@app.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    """Internal endpoint — called by other services to create a notification."""
    notif = Notification(user_id=payload.user_id, message=payload.message)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


@app.get("/notifications", response_model=list[NotificationResponse])
def list_my_notifications(user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@app.patch("/notifications/{notif_id}/read", response_model=NotificationResponse)
def mark_as_read(notif_id: int, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif
