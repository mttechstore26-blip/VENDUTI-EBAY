"""Run the eBay collector only if at least 11 free subscription requests remain.

No API key or database is written to GitHub. Fail closed on usage errors.
"""
import os
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
key = os.getenv("SOLDCOMPS_API_KEY", "").strip()
if not key or key == "sc_INSERISCI_QUI":
    sys.exit("ERRORE: chiave SoldComps non configurata")

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

print(f"Saldo SoldComps: {remaining} richieste; riserva: {reserve}. Avvio raccolta di una pagina.", flush=True)
env = os.environ.copy()
env["MAX_PAGES_PER_RUN"] = "1"
result = subprocess.run([sys.executable, str(ROOT / "collector.py")], cwd=ROOT, env=env, check=False)
sys.exit(result.returncode)
