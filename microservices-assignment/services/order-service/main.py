from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os
import psycopg2

app = FastAPI(title="Order Service")

load_dotenv()

DB_NAME = os.getenv("POSTGRES_DB", "postgres_db")
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "password")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def get_db_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
        )
    except Exception as exc:
        print(f"Database connection error: {exc}")
        raise HTTPException(status_code=503, detail="Database service unavailable.")

def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                total DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
    except Exception as exc:
        print(f"Error during DB initialization: {exc}")
    finally:
        if conn:
            conn.close()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def read_root():
    return {"service": "OrderService", "status": "Operational", "db_host": DB_HOST}

@app.post("/place-order")
async def place_order(user_id: int, product_id: int, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        total_cost = float(quantity * 10)
        cursor.execute(
            """
            INSERT INTO orders (user_id, product_id, quantity, total)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (user_id, product_id, quantity, total_cost),
        )
        order_id = cursor.fetchone()[0]
        conn.commit()
        return {
            "message": "Order placed successfully",
            "order_details": {
                "id": order_id,
                "user_id": user_id,
                "product_id": product_id,
                "quantity": quantity,
                "total": total_cost,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to place order: {exc}")
    finally:
        if conn:
            conn.close()

@app.get("/metrics")
def metrics():
    metric = "order_service_orders_total 1\n"
    return PlainTextResponse(metric, media_type="text/plain")
