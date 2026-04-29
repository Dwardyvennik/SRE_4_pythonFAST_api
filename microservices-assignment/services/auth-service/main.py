from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
import time
import random

app = FastAPI(title="Auth Service")

# Basic in-memory storage simulation
users = {
    "user1": {"password": "secure_pass", "role": "user"}
}

@app.get("/")
def read_root():
    return {"service": "AuthService", "status": "Operational"}

@app.post("/login")
async def login(request: Request):
    # Simulating basic authentication check (no hashing, for assignment simplicity)
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    if username in users and users[username]["password"] == password:
        # Fake JWT generation simulation
        jwt = f"fake-jwt-{int(time.time())}-{random.randint(100, 999)}"
        return {"access_token": jwt, "token_type": "bearer", "role": users[username]["role"]}

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/metrics")
def metrics():
    # Simple endpoint to expose a metric for Prometheus
    metric = 'auth_service_requests_total{status="success"} 1\n'
    return PlainTextResponse(metric, media_type="text/plain")

