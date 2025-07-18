import hmac
import hashlib
from fastapi import FastAPI, WebSocket, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()
clients = set()
GITHUB_SECRET = b"CHANGE_ME_SECRET"  # À personnaliser et à synchroniser avec le webhook GitHub

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except Exception:
        clients.discard(websocket)

def verify_github_signature(payload, signature):
    if not signature:
        return False
    mac = hmac.new(GITHUB_SECRET, msg=payload, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/github-webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    body = await request.body()
    if not verify_github_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid signature")
    data = await request.json()
    # Diffuse à tous les clients connectés
    for ws in list(clients):
        try:
            await ws.send_json({"type": "update", "data": data})
        except Exception:
            clients.discard(ws)
    return JSONResponse({"status": "ok"}) 