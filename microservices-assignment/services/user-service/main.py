from fastapi import FastAPI, Request
import time
import random

app = FastAPI()

# In-memory storage simulation
users_db = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"}
}

@app.get("/")
def read_root():
    return {"service": "UserService", "status": "Operational"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    if user_id in users_db:
        return users_db[user_id]
    return {"message": "User not found"}, 404

@app.post("/users/")
async def create_user(name: str, email: str):
    # Simulate creation and ID assignment
    new_id = max(users_db.keys()) + 1
    users_db[new_id] = {"id": new_id, "name": name, "email": email}
    return users_db[new_id]

@app.get("/metrics")
def metrics():
    metric = f'user_service_requests_total{{"endpoint":"/users/{random.randint(1, 2)}"}} 1\n'
    return {"text/plain": metric}
