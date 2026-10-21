"""Backfill used Italian Apple laptops (eBay category 111422), 150-300 EUR.

Fetch sold listings from 2026-09-01 through 2026-10-21, inclusive.
Resumable; quota checked before EVERY request, no extra-credit API charges.
Does not delete existing rows or send Telegram notifications.
"""
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from collector import API, connect, number

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
STATE = ROOT / "data" / "apple_111422_150_300_it_sep2026.state"
START = "2026-09-01"
END = "2026-10-21"
CATEGORY_ID = "111422"
CATEGORY_NAME = "PORTATILI APPLE 150-300 🇮🇹"
RESERVE = 10
MAX_PAGES_PER_INVOCATION = 100
HEADERS = {"X-Credit-Source": "subscription-only"}


def main():
    key = os.getenv("SOLDCOMPS_API_KEY", "").strip()
    if not key:
        sys.exit("ERRORE: chiave SoldComps mancante")
    auth = {"Authorization": f"Bearer {key}"}
    page = 1
    if STATE.exists():
        saved = STATE.read_text().strip()
        if saved == "COMPLETE":
            print("COMPLETE: backfill già terminato fino al 1 settembre.")
            return
        page = int(saved)
        if page < 1:
            sys.exit("Stato backfill non valido")

    db = connect()
    db.execute(
        "INSERT INTO categories(category_id,name) VALUES (?,?) "
        "ON CONFLICT(category_id) DO UPDATE SET name=excluded.name",
        (CATEGORY_ID, CATEGORY_NAME),
    )
    db.commit()

    pages_read = rows_seen = rows_added = 0
    try:
        with requests.Session() as session:
            for _ in range(MAX_PAGES_PER_INVOCATION):
                try:
                    usage = session.get(
                        "https://api.sold-comps.com/usage",
                        headers=auth,
                        timeout=(5, 12),
                    )
                    usage.raise_for_status()
                    remaining = int(usage.json()["usage"]["remaining"])
                except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
                    print(f"STOP: quota non verificabile ({type(exc).__name__}). Nessuna pagina consumata.", flush=True)
                    return

                if remaining <= RESERVE:
                    print(f"STOP: {remaining} crediti residui, riserva {RESERVE}. Riprendere quando disponibili.", flush=True)
                    return

                params = {
                    "categoryId": CATEGORY_ID,
                    "ebaySite": "ebay.it",
                    "page": page,
                    "count": 240,
                    "sortOrder": "endedRecently",
                    "minPrice": 150,
                    "maxPrice": 300,
                    "conditionId": 3000,
                    "itemLocation": "domestic",
                }
                try:
                    response = session.get(
                        API, params=params,
                        headers={**auth, **HEADERS},
                        timeout=70,
                    )
                    if response.status_code == 429:
                        print("STOP: SoldComps restituisce 429. Nessun credito extra richiesto.")
                        return
                    response.raise_for_status()
                    payload = response.json()
                    items = payload.get("items", [])
                    if not isinstance(items, list):
                        raise ValueError("items non è una lista")
                except (requests.RequestException, ValueError) as exc:
                    print(f"STOP pagina {page}: {type(exc).__name__}: {exc}. Pagina da riprovare.", flush=True)
                    return

                if not items:
                    STATE.parent.mkdir(parents=True, exist_ok=True)
                    STATE.write_text("COMPLETE")
                    print("COMPLETE: nessun altro annuncio restituito.")
                    return

                dates = []
                inserted = 0
                for item in items:
                    ended = str(item.get("endedAt") or "")[:10]
                    if not ended:
                        continue
                    dates.append(ended)
                    if not (START <= ended <= END):
                        continue
                    price = number(item.get("soldPrice"))
                    if price is None or not 150 <= price <= 300:
                        continue
                    item_id = str(item.get("itemId") or "")
                    if not item_id:
                        continue
                    now = datetime.now(timezone.utc).isoformat()
                    cur = db.execute(
                        """INSERT OR IGNORE INTO sales
                        (site,item_id,title,url,image,ended_at,sold_price,currency,
                         shipping_price,total_price,condition,seller,buying_format,
                         best_offer_accepted,scraped_at,first_seen,category_id,item_location)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            "ebay.it:111422", item_id, item.get("title"), item.get("url"),
                            item.get("thumbnailUrl"), item.get("endedAt"), price,
                            item.get("soldCurrency"), number(item.get("shippingPrice")),
                            number(item.get("totalPrice")), item.get("condition"),
                            item.get("sellerUsername"), item.get("buyingFormat"),
                            int(bool(item.get("bestOfferAccepted"))),
                            item.get("scrapedAt"), now, CATEGORY_ID,
                            str(item.get("itemLocation") or ""),
                        ),
                    )
                    inserted += int(cur.rowcount > 0)
                db.commit()
                pages_read += 1
                rows_seen += len(items)
                rows_added += inserted

                if not dates:
                    print(f"STOP pagina {page}: date endedAt assenti; controllo manuale necessario.")
                    return

                # Stop ONLY if the newest dated item on the page is before the cutoff.
                # A single older listing among newer results does not end the backfill.
                reached_start = max(dates) < START
                finished = reached_start or not payload.get("hasNextPage", False)
                STATE.parent.mkdir(parents=True, exist_ok=True)
                STATE.write_text("COMPLETE" if finished else str(page + 1))
                print(
                    f"Pagina {page}: {len(items)} visti, {inserted} nuovi, "
                    f"date {min(dates)}..{max(dates)}, "
                    f"quota prima={remaining}, "
                    f"{'COMPLETE' if finished else 'continua'}",
                    flush=True,
                )
                if finished:
                    print(f"FINE: {pages_read} pagine, {rows_seen} analizzati, {rows_added} nuovi inseriti.")
                    return
                page += 1
                time.sleep(3)
    finally:
        db.close()
    print(f"PAUSA: raggiunte {MAX_PAGES_PER_INVOCATION} pagine. "
          f"Totale nuovi {rows_added}. Riesegui lo script per proseguire.")


if __name__ == "__main__":
    main()
