"""Quota-safe category-wide SoldComps scheduler.

Giocattoli e modellismo every six hours (00,06,12,18).
Other categories retain their existing daily slots. Respect monthly reserve.
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
key = os.getenv("SOLDCOMPS_API_KEY", "").strip()
if not key or key == "sc_INSERISCI_QUI":
    sys.exit("ERRORE: chiave SoldComps non configurata")

hour = datetime.now().hour
slots = {
    0: [("141755", "Album sportivi", "70"), ("220", "Giocattoli e modellismo", "100")],
    6: [("220", "Giocattoli e modellismo", "100")],
    12: [("63", "Fumetti e memorabilia", "100"), ("220", "Giocattoli e modellismo", "100")],
    18: [("220", "Giocattoli e modellismo", "100")],
}
jobs = slots.get(hour, [])
if not jobs:
    print(f"Ore {hour:02d}: nessuna raccolta prevista.")
    sys.exit(0)

try:
    response = requests.get(
        "https://api.sold-comps.com/usage",
        headers={"Authorization": f"Bearer {key}"},
        timeout=(5, 12),
    )
    response.raise_for_status()
    remaining = int(response.json()["usage"]["remaining"])
except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
    print(f"Raccolta sospesa: impossibile verificare la quota ({type(exc).__name__}).")
    sys.exit(0)

reserve = 10
failures = 0
for category_id, category_name, min_price in jobs:
    if remaining <= reserve:
        print(f"Raccolta sospesa: {remaining} richieste residue; riserva {reserve}.")
        break
    print(f"Quota stimata {remaining}; categoria {category_name} ({category_id}), minimo {min_price} EUR.", flush=True)
    env = os.environ.copy()
    env.update({
        "EBAY_CATEGORY_ID": category_id,
        "EBAY_CATEGORY_NAME": category_name,
        "MIN_PRICE": min_price,
        "MAX_PAGES_PER_RUN": "1",
    })
    result = subprocess.run([sys.executable, str(ROOT / "collector.py")],
                            cwd=ROOT, env=env, check=False)
    if result.returncode:
        failures += 1
        # Stop rather than risk consuming repeated credits after an API error.
        break
    remaining -= 1

sys.exit(1 if failures else 0)
