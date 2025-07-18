import threading
import time
import logging
import os
import sys
import subprocess

SERVICE_DEFS = {
    "auto_sync": {
        "type": "process",
        "path": os.path.join(os.path.dirname(__file__), "auto_sync.py"),
        "args": [sys.executable],
    },
    "notify": {
        "type": "process",
        "path": os.path.join(os.path.dirname(__file__), "notifier_client.py"),
        "args": [sys.executable],
    },
    "telemetry": {
        "type": "thread",
        "target": "telemetry_client.start_telemetry_client",
    },
}

service_procs = {}
service_threads = {}
service_status = {k: {"status": "unknown", "restarts": 0, "last_error": None} for k in SERVICE_DEFS}

# Pour threads Python, on ne peut pas vraiment les relancer proprement, donc on surveille surtout les process

def start_service(name):
    conf = SERVICE_DEFS[name]
    if conf["type"] == "process":
        if not os.path.exists(conf["path"]):
            service_status[name]["status"] = "absent"
            return
        proc = subprocess.Popen(conf["args"] + [conf["path"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        service_procs[name] = proc
        service_status[name]["status"] = "running"
    elif conf["type"] == "thread":
        # Pour la télémétrie, on relance le thread si besoin
        import importlib
        mod_name, func_name = conf["target"].rsplit(".", 1)
        mod = importlib.import_module(mod_name)
        t = threading.Thread(target=getattr(mod, func_name), daemon=True)
        t.start()
        service_threads[name] = t
        service_status[name]["status"] = "running"

def stop_service(name):
    conf = SERVICE_DEFS[name]
    if conf["type"] == "process":
        proc = service_procs.get(name)
        if proc and proc.poll() is None:
            proc.terminate()
            service_status[name]["status"] = "stopped"
    elif conf["type"] == "thread":
        # Pas d'arrêt propre pour les threads
        service_status[name]["status"] = "stopped"

def monitor_services(interval=5):
    while True:
        for name, conf in SERVICE_DEFS.items():
            if conf["type"] == "process":
                proc = service_procs.get(name)
                if proc:
                    if proc.poll() is not None:
                        # Crash détecté
                        service_status[name]["status"] = "crashed"
                        service_status[name]["restarts"] += 1
                        service_status[name]["last_error"] = f"Code retour: {proc.returncode}"
                        logging.warning(f"Service {name} crashé, relance...")
                        start_service(name)
                else:
                    # Pas lancé, on tente de lancer
                    start_service(name)
            elif conf["type"] == "thread":
                t = service_threads.get(name)
                if t and not t.is_alive():
                    service_status[name]["status"] = "crashed"
                    service_status[name]["restarts"] += 1
                    service_status[name]["last_error"] = "Thread mort"
                    logging.warning(f"Thread {name} mort, relance...")
                    start_service(name)
        time.sleep(interval)

def start_monitor():
    t = threading.Thread(target=monitor_services, daemon=True)
    t.start()

def get_status_report():
    report = []
    for name, st in service_status.items():
        report.append(f"{name}: {st['status']} (restarts: {st['restarts']}, last_error: {st['last_error']})")
    return "\n".join(report) 