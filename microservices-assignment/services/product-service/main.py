from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import random

app = FastAPI(title="Product Service")

products_db = {
    1: {"id": 1, "name": "Laptop", "price": 999.99, "stock": 12},
    2: {"id": 2, "name": "Keyboard", "price": 79.99, "stock": 35},
    3: {"id": 3, "name": "Mouse", "price": 39.99, "stock": 50},
}

@app.get("/")
def read_root():
    return {"service": "ProductService", "status": "Operational"}

@app.get("/products/")
async def list_products():
    return list(products_db.values())

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    if product_id in products_db:
        return products_db[product_id]
    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/products/")
async def create_product(name: str, price: float, stock: int = 0):
    new_id = max(products_db.keys()) + 1
    products_db[new_id] = {"id": new_id, "name": name, "price": price, "stock": stock}
    return products_db[new_id]

@app.get("/metrics")
def metrics():
    metric = f'product_service_requests_total{{endpoint="/products/{random.randint(1, 3)}"}} 1\n'
    return PlainTextResponse(metric, media_type="text/plain")
