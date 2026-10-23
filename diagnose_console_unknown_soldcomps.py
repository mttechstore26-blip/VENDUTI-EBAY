"""Read-only five-item SoldComps location verification pilot.

Budget: maximum 5 /v1/item calls (nominally one credit each), never retries.
Checks available quota and preserves a 10-credit reserve.
No writes to SQLite, state files, or other local files.
"""
import os
import sqlite3
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from eu_locations import is_eu_location

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DB = (ROOT / os.getenv("DB_PATH", "./data/ebay_sold.db")).resolve()
API_ROOT = "https://api.sold-comps.com"
RESERVE = 10
MAX_CREDITS = 5
# Ground truth verified manually by the user on the eBay item pages.
SAMPLES = [
    ("960071387531", "Italia"),
    ("267802796302", "Stati Uniti"),
    ("820091706350", "Stati Uniti"),
    ("377504428514", "Stati Uniti"),
    ("168799276572", "Stati Uniti"),
]


def main():
    if not DB.is_file():
        sys.exit("Database non trovato: nessuna richiesta inviata")
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as conn:
        archived = {str(row[0]) for row in conn.execute(
            "SELECT item_id FROM console_300_eu_excluded WHERE item_id IN (?,?,?,?,?)",
            tuple(item_id for item_id, _ in SAMPLES))}
    if len(archived) != len(SAMPLES):
        missing = [item_id for item_id, _ in SAMPLES if item_id not in archived]
        sys.exit(f"Test annullato: ID non presenti nell'archivio: {missing}")

    key = os.getenv("SOLDCOMPS_API_KEY", "").strip()
    if not key:
        sys.exit("Chiave SoldComps assente: nessuna richiesta inviata")
    headers = {
        "Authorization": f"Bearer {key}",
        "X-Credit-Source": "subscription-only",
    }
    try:
        usage = requests.get(API_ROOT + "/usage", headers=headers, timeout=(5, 12))
        usage.raise_for_status()
        remaining = int(usage.json()["usage"]["remaining"])
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        sys.exit(f"Quota non verificabile ({type(exc).__name__}): nessuna richiesta agli annunci")
    if remaining < MAX_CREDITS + RESERVE:
        sys.exit(f"Test annullato: quota {remaining}, servono almeno {MAX_CREDITS + RESERVE}")

    print(f"Quota iniziale: {remaining}; massimo {MAX_CREDITS} crediti per annunci; riserva {RESERVE}")
    print("MODALITA' SOLA LETTURA: nessun aggiornamento al database.")
    made = 0
    recognized = 0
    for item_id, verified_country in SAMPLES[:MAX_CREDITS]:
        # One item call, no retry and no description hydration.
        made += 1
        try:
            response = requests.get(
                f"{API_ROOT}/v1/item/{item_id}",
                params={"ebaySite": "ebay.it", "includeDescription": "false"},
                headers=headers, timeout=(5, 30))
        except requests.RequestException as exc:
            print(f"{item_id}: errore rete {type(exc).__name__}; stop")
            break
        if response.status_code in (401, 402, 403, 429):
            print(f"{item_id}: HTTP {response.status_code}; stop")
            break
        if response.status_code != 200:
            print(f"{item_id}: HTTP {response.status_code}; nessuna località confermata")
            continue
        try:
            payload = response.json()
        except ValueError:
            print(f"{item_id}: risposta JSON non valida; stop")
            break
        data = payload.get("item", payload) if isinstance(payload, dict) else {}
        if not isinstance(data, dict):
            data = {}
        location = data.get("location") or data.get("itemLocation")
        recognized += int(bool(str(location or "").strip()))
        print(f"{item_id} | conferma manuale={verified_country} | "
              f"SoldComps={location!r} | UE={is_eu_location(location)}")
    print(f"RISULTATO: chiamate articolo={made}/{MAX_CREDITS}; "
          f"località compilate={recognized}; nessun dato modificato.")
    print("Il consumo effettivo va verificato nel pannello usage SoldComps.")


if __name__ == "__main__":
    main()
