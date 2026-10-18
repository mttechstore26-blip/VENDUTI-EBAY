"""Quota-safe SoldComps scheduler for three category-wide monitors.

The existing six-hour systemd timer remains enabled; two daily slots and one alternate-day slot
make an API call, keeping the free plan viable until its monthly reset.
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

# Server timezone determines calendar slots. Third category runs at 18:00 on even dates to protect the 100-request monthly plan.
hour = datetime.now().hour
slots = {
    0: ("141755", "Album sportivi", "70"),
    12: ("63", "Fumetti e memorabilia", "100"),
    18: ("220", "Giocattoli e modellismo", "70"),
}
if hour not in slots or (hour == 18 and datetime.now().day % 2 != 0):
    print(f"Ore {hour:02d}:00: nessuna raccolta programmata (quota gratuita conservata).")
    sys.exit(0)

category_id, category_name, min_price = slots[hour]

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
if remaining <= reserve:
    print(f"Raccolta sospesa: {remaining} richieste residue, riserva di {reserve}.")
    sys.exit(0)

print(
    f"Saldo {remaining}; categoria {category_name} ({category_id}); minimo {min_price} EUR; una pagina.",
    flush=True,
)
env = os.environ.copy()
env.update({
    "EBAY_CATEGORY_ID": category_id,
    "EBAY_CATEGORY_NAME": category_name,
    "MIN_PRICE": min_price,
    "MAX_PAGES_PER_RUN": "1",
})
result = subprocess.run(
    [sys.executable, str(ROOT / "collector.py")],
    cwd=ROOT,
    env=env,
    check=False,
)
sys.exit(result.returncode)
