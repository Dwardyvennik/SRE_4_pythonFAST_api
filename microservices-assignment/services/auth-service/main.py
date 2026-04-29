from fastapi import FastAPI, Request
import time
import random

app = FastAPI()

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

    if username == "user1" and password == "secure_pass":
        # Fake JWT generation simulation
        jwt = f"fake-jwt-{int(time.time())}-{random.randint(100, 999)}"
        return {"access_token": jwt, "token_type": "bearer"}
    else:
        return {"message": "Invalid credentials"}, 401

@app.get("/metrics")
def metrics():
    # Simple endpoint to expose a metric for Prometheus
    metric = f'auth_service_requests_total{{"status":"success"}} 1\n'
    return {"text/plain": metric}

