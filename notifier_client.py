import threading
import time
import websocket
import json
import logging
from live_updater import LiveUpdater

SERVER_URL = "ws://localhost:8000/ws"  # À personnaliser avec l'adresse de ton serveur

def on_message(ws, message):
    data = json.loads(message)
    if data.get("type") == "update":
        logging.info("Signal reçu : mise à jour GitHub détectée")
        updater = LiveUpdater(None)
        updater.check_for_updates_silent()

def run_ws_client():
    while True:
        try:
            ws = websocket.WebSocketApp(
                SERVER_URL,
                on_message=on_message
            )
            ws.run_forever()
        except Exception as e:
            logging.warning(f"Erreur WebSocket, reconnexion dans 10s : {e}")
            time.sleep(10)

def start_notifier_client():
    t = threading.Thread(target=run_ws_client, daemon=True)
    t.start() 