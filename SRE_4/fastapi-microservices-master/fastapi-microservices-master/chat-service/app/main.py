import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, create_engine, or_
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/microservices_db")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
security = HTTPBearer()


class Message(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, nullable=False, index=True)
    receiver_id = Column(Integer, nullable=False, index=True)
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MessagePayload(BaseModel):
    receiver_id: int
    content: str = Field(min_length=1, max_length=1000)


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
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


def message_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        created_at=message.created_at,
    )


app = FastAPI(title="Chat Service", openapi_url="/chat/openapi.json", docs_url="/chat/docs")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/chat/health")
def health():
    return {"status": "ok", "service": "chat-service"}


@app.post("/chat/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(payload: MessagePayload, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    message = Message(sender_id=user_id, receiver_id=payload.receiver_id, content=payload.content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message_response(message)


@app.get("/chat/messages", response_model=list[MessageResponse])
def list_messages(
    with_user_id: int | None = Query(default=None),
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db),
):
    query = db.query(Message).filter(or_(Message.sender_id == user_id, Message.receiver_id == user_id))
    if with_user_id is not None:
        query = query.filter(or_(Message.sender_id == with_user_id, Message.receiver_id == with_user_id))
    messages = query.order_by(Message.created_at.desc()).all()
    return [message_response(message) for message in messages]
