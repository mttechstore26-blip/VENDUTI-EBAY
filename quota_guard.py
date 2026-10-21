"""Quota-safe category-wide SoldComps scheduler.

Twelve monitored categories every six hours (00,06,12,18).
Respect monthly reserve and refuse extra-credit API charges.
"""
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
key = os.getenv("SOLDCOMPS_API_KEY", "").strip()
if not key or key == "sc_INSERISCI_QUI":
    sys.exit("ERRORE: chiave SoldComps non configurata")

# Retire legacy macro-category 220 once, including stored sales, with a database backup.
def retire_legacy_category():
    db = (ROOT / os.getenv("DB_PATH", "./data/ebay_sold.db")).resolve()
    if not db.is_file():
        return
    backup_file = db.with_name(db.name + ".before_retire_220")
    with sqlite3.connect(db, timeout=20) as con:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='categories'").fetchone():
            return
        exists = con.execute("SELECT 1 FROM categories WHERE category_id='220'").fetchone()
        if not exists:
            return
        if not backup_file.exists():
            with sqlite3.connect(backup_file) as backup:
                con.backup(backup)
        deleted = con.execute("DELETE FROM sales WHERE category_id='220'").rowcount
        con.execute("DELETE FROM categories WHERE category_id='220'")
        con.commit()
        print(f"Rimossa categoria 220 e {deleted} vendite obsolete; backup: {backup_file.name}", flush=True)

retire_legacy_category()

hour = datetime.now().hour
categories = [
    ("141755", "Album sportivi", "70"),
    ("63", "Fumetti e memorabilia", "100"),
    ("717", "Giocattoli d\u0027epoca", "100"),
    ("233", "Giochi di società", "100"),
    ("183446", "Costruzioni", "100"),
    ("101376", "Bambole vintage", "160"),
    ("20667", "Piccoli elettrodomestici per la cucina", "100"),
    ("38250", "Macchine da caffè", "100"),
    ("139971", "CONSOLE 400+", "400"),
    ("111422", "PORTATILI APPLE 150-300 🇮🇹", "150"),
    ("175672", "PORTATILI 150-300", "150"),
    ("80053", "Monitor usati Italia 100-300", "100"),
]
slots = {hour_slot: categories for hour_slot in (0, 6, 12, 18)}
jobs = slots.get(hour, [])
if not jobs:
    print(f"Ore {hour:02d}: nessuna raccolta prevista.")
    sys.exit(0)

# Retry only transient connection failures before any category requests are sent.
# Authentication, quota and malformed-response errors must not trigger retries.
remaining = None
for attempt in range(1, 4):
    try:
        response = requests.get(
            "https://api.sold-comps.com/usage",
            headers={"Authorization": f"Bearer {key}"},
            timeout=(5, 12),
        )
        response.raise_for_status()
        remaining = int(response.json()["usage"]["remaining"])
        break
    except (requests.ConnectionError, requests.Timeout) as exc:
        print(f"Verifica quota: tentativo {attempt}/3 fallito ({type(exc).__name__}).", flush=True)
        if attempt < 3:
            time.sleep(5)
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        print(f"Raccolta sospesa: impossibile verificare la quota ({type(exc).__name__}).", flush=True)
        sys.exit(1)

if remaining is None:
    print("Raccolta sospesa: verifica quota non riuscita dopo 3 tentativi.", flush=True)
    sys.exit(1)

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
    # Per-category filters: avoid leaking limits into other categories.
    env.pop("EBAY_CONDITION_ID", None)
    env.pop("MAX_PRICE", None)
    env.pop("EBAY_ITEM_LOCATION", None)
    if category_id in ("20667", "38250", "139971", "111422", "175672", "80053"):
        env["EBAY_CONDITION_ID"] = "3000"
    if category_id in ("63", "111422", "175672", "80053"):
        # For ebay.it, domestic restricts item location to Italy.
        env["EBAY_ITEM_LOCATION"] = "domestic"
    if category_id == "175672":
        env["MAX_PRICE"] = "300"
    if category_id in ("38250", "80053", "111422"):
        env["MAX_PRICE"] = "300"
    result = subprocess.run([sys.executable, str(ROOT / "collector.py")],
                            cwd=ROOT, env=env, check=False)
    if result.returncode:
        failures += 1
        # Stop rather than risk consuming repeated credits after an API error.
        break
    remaining -= 1

sys.exit(1 if failures else 0)
