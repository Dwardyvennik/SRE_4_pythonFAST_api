from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import time

app = FastAPI(title="Chat Service")

@app.get("/")
def read_root():
    return {"service": "ChatService", "status": "Operational"}

@app.post("/send-message")
async def send_message(sender: str, recipient: str, message: str):
    # Simulating saving a message without persistent storage.
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return {
        "status": "Message sent successfully",
        "message_details": f"[{timestamp}] '{sender}' -> '{recipient}': {message}",
    }

@app.get("/metrics")
def metrics():
    metric = "chat_service_messages_sent_total 1\n"
    return PlainTextResponse(metric, media_type="text/plain")
