"""One-off historical backfill: used domestic laptops sold Sep 1-Oct 19 2026.
Category-only, without keyword. Begins at page 2 (page 1 already collected).
Each call checks subscription quota and preserves reserve; safe to rerun.
"""
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
from collector import API, connect, number

CATEGORY = "175672"
NAME = "PORTATILI 150-300"
SINCE, THROUGH = "2026-09-01", "2026-10-19"
FIRST_PAGE = int(os.getenv("BACKFILL_START_PAGE", "2"))
LAST_PAGE = int(os.getenv("BACKFILL_END_PAGE", "60"))
RESERVE = 100

key = os.getenv("SOLDCOMPS_API_KEY", "").strip()
if not key:
    raise SystemExit("SOLDCOMPS_API_KEY assente nel file .env")
headers = {"Authorization": f"Bearer {key}", "X-Credit-Source": "subscription-only"}
session = requests.Session()
db = connect()
db.execute("INSERT INTO categories(category_id,name) VALUES (?,?) ON CONFLICT(category_id) DO UPDATE SET name=excluded.name", (CATEGORY, NAME))
db.commit()
inserted = scanned = calls = 0
try:
    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        usage = session.get("https://api.sold-comps.com/usage",
                            headers={"Authorization": f"Bearer {key}"}, timeout=15)
        usage.raise_for_status()
        remaining = int(usage.json()["usage"]["remaining"])
        if remaining <= RESERVE:
            print(f"STOP quota: {remaining}, riserva {RESERVE}", flush=True)
            break
        params = {"categoryId": CATEGORY, "ebaySite": "ebay.it", "page": page,
                  "count": 240, "sortOrder": "endedRecently", "minPrice": 150, "maxPrice": 300,
                  "conditionId": 3000, "itemLocation": "domestic"}
        response = session.get(API, params=params, headers=headers, timeout=70)
        if response.status_code == 429:
            print("STOP: quota API (429)", flush=True)
            break
        response.raise_for_status()
        calls += 1
        payload = response.json()
        items = payload.get("items", [])
        scanned += len(items)
        dates = []
        added = 0
        for item in items:
            day = str(item.get("endedAt") or "")[:10]
            if day: dates.append(day)
            if not (SINCE <= day <= THROUGH):
                continue
            price = number(item.get("soldPrice"))
            if price is None or price < 150 or price > 300:
                continue
            item_id = str(item.get("itemId") or "")
            if not item_id:
                continue
            now = datetime.now(timezone.utc).isoformat()
            loc = item.get("itemLocation")
            cur = db.execute("""INSERT OR IGNORE INTO sales
                (site,item_id,title,url,image,ended_at,sold_price,currency,shipping_price,total_price,
                 condition,seller,buying_format,best_offer_accepted,scraped_at,first_seen,category_id,item_location)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("ebay.it",item_id,item.get("title"),item.get("url"),item.get("thumbnailUrl"),
                 item.get("endedAt"),price,item.get("soldCurrency"),number(item.get("shippingPrice")),
                 number(item.get("totalPrice")),item.get("condition"),item.get("sellerUsername"),
                 item.get("buyingFormat"),int(bool(item.get("bestOfferAccepted"))),
                 item.get("scrapedAt"),now,CATEGORY,str(loc) if loc else None))
            added += cur.rowcount
        db.commit()
        inserted += added
        print(f"Pagina {page}: {len(items)} annunci, date {min(dates) if dates else 'N/D'} -> {max(dates) if dates else 'N/D'}, nuovi {added}, totale nuovi {inserted}, quota precedente {remaining}", flush=True)
        if dates and max(dates) < SINCE:
            print("STOP: pagina interamente antecedente al 1 ottobre.", flush=True)
            break
        if not items or not payload.get("hasNextPage"):
            print("STOP: nessuna pagina successiva.", flush=True)
            break
        time.sleep(3)
except KeyboardInterrupt:
    print("Interrotto: i risultati delle pagine completate rimangono salvati.", flush=True)
finally:
    print(f"RISULTATO: {calls} richieste, {scanned} annunci esaminati, {inserted} nuovi salvati.", flush=True)
    db.close()
