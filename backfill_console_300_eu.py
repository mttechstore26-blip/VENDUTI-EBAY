"""Quota-safe one-page-per-invocation console EU backfill from 1 August 2026."""
import os
import sys
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv
from collector import API, connect, number
from eu_locations import is_eu_location

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
STATE = ROOT / "data/console_300_eu_aug2026_v2.state"
CUTOFF = "2026-08-01"
RESERVE = 10

def main():
    if STATE.exists() and STATE.read_text().strip() == "COMPLETE":
        print("COMPLETE: paginazione terminata per storico dal 1 agosto")
        return
    page = int(STATE.read_text().strip()) if STATE.exists() else 1
    key = os.getenv("SOLDCOMPS_API_KEY", "").strip()
    if not key:
        sys.exit("Chiave API assente")
    try:
        r = requests.get("https://api.sold-comps.com/usage",
            headers={"Authorization": f"Bearer {key}"}, timeout=(5, 12))
        r.raise_for_status()
        remaining = int(r.json()["usage"]["remaining"])
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        sys.exit("Quota non verificabile: " + str(exc))
    if remaining <= RESERVE:
        print(f"STOP: quota {remaining}, riserva {RESERVE}")
        return
    args = {"categoryId": "139971", "ebaySite": "ebay.it",
            "page": page, "count": 240, "sortOrder": "endedRecently",
            "minPrice": 300, "conditionId": 3000}
    try:
        resp = requests.get(API, params=args,
            headers={"Authorization": f"Bearer {key}",
                     "X-Credit-Source": "subscription-only"}, timeout=70)
        if resp.status_code == 429:
            print("Quota esaurita, pagina invariata")
            return
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        sys.exit("Richiesta fallita, pagina invariata: " + str(exc))
    items = payload.get("items", [])
    if items and not any(i.get("endedAt") for i in items):
        sys.exit("Date assenti: pagina invariata")
    # Diagnostic on the very same API response; zero additional requests.
    dated = [str(item.get("endedAt") or "")[:10] for item in items if item.get("endedAt")]
    months = Counter(d[:7] for d in dated)
    known_eu = sum(is_eu_location(i.get("itemLocation")) for i in items)
    unknown_loc = sum(not str(i.get("itemLocation") or "").strip() for i in items)
    known_non_eu = len(items) - known_eu - unknown_loc
    print(f"[DIAGNOSTICA] Pagina {page} | date: "
          f"{min(dated) if dated else 'N/D'} → {max(dated) if dated else 'N/D'} "
          f"| mesi: {dict(sorted(months.items()))}")
    print(f"[DIAGNOSTICA] Località: UE={known_eu}, "
          f"extra-UE/non riconosciuta={known_non_eu}, "
          f"assente={unknown_loc} | hasNextPage={payload.get('hasNextPage')}")
    db = connect()
    db.execute("""INSERT INTO categories(category_id,name)
        VALUES('139971','CONSOLE 300+ 🇪🇺')
        ON CONFLICT(category_id) DO UPDATE SET name=excluded.name""")
    inserted = 0
    for item in items:
        ended = str(item.get("endedAt") or "")
        price = number(item.get("soldPrice"))
        loc = item.get("itemLocation")
        if not ended or ended[:10] < CUTOFF or price is None or price < 300 or not is_eu_location(loc):
            continue
        item_id = str(item.get("itemId") or "")
        if not item_id:
            continue
        now = datetime.now(timezone.utc).isoformat()
        cursor = db.execute("""INSERT OR IGNORE INTO sales
          (site,item_id,title,url,image,ended_at,sold_price,currency,shipping_price,total_price,
           condition,seller,buying_format,best_offer_accepted,scraped_at,first_seen,category_id,item_location)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          ("ebay.it", item_id, item.get("title"), item.get("url"), item.get("thumbnailUrl"),
           ended, price, item.get("soldCurrency"), number(item.get("shippingPrice")),
           number(item.get("totalPrice")), item.get("condition"), item.get("sellerUsername"),
           item.get("buyingFormat"), int(bool(item.get("bestOfferAccepted"))),
           item.get("scrapedAt"), now, "139971", str(loc)))
        inserted += int(cursor.rowcount > 0)
    db.commit()
    db.close()
    # Results can mix sale dates within a page: an older item does not prove
    # all subsequent pages are older. Follow API pagination to exhaustion.
    complete = not payload.get("hasNextPage", False) or not items
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text("COMPLETE" if complete else str(page + 1))
    print(f"Pagina {page}: {len(items)} risultati, {inserted} console UE aggiunte; "
          f"prossimo stato: {'COMPLETE' if complete else page + 1}; quota prima {remaining}")

if __name__ == "__main__":
    main()
