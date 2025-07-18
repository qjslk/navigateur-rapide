import os
import sys
import time
import threading
import json
import logging
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

class ConfigChangeHandler:
    def __init__(self, on_change):
        self.on_change = on_change
        self.last_config = self.load_config()

    def load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def check_and_reload(self):
        new_config = self.load_config()
        if new_config != self.last_config:
            logging.info("Changement de config détecté, application à chaud...")
            self.on_change(new_config, self.last_config)
            self.last_config = new_config

    def start_polling(self, interval=2):
        while True:
            self.check_and_reload()
            time.sleep(interval)

if HAS_WATCHDOG:
    class WatchdogHandler(FileSystemEventHandler):
        def __init__(self, on_change, handler):
            super().__init__()
            self.on_change = on_change
            self.handler = handler
        def on_modified(self, event):
            if event.src_path.endswith("config.json"):
                self.handler.check_and_reload()

def start_config_watcher(on_change):
    handler = ConfigChangeHandler(on_change)
    if HAS_WATCHDOG:
        observer = Observer()
        event_handler = WatchdogHandler(on_change, handler)
        observer.schedule(event_handler, os.path.dirname(CONFIG_PATH), recursive=False)
        observer.start()
        logging.info("Surveillance de config.json (watchdog)")
        t = threading.Thread(target=observer.join, daemon=True)
        t.start()
    else:
        logging.info("Surveillance de config.json (polling)")
        t = threading.Thread(target=handler.start_polling, daemon=True)
        t.start() 