"""One-off, quota-limited historical backfill for category 20667 until 2026-10-01."""
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
os.environ.update({"EBAY_CATEGORY_ID":"20667", "EBAY_CATEGORY_NAME":"Piccoli elettrodomestici per la cucina", "MIN_PRICE":"100", "EBAY_CONDITION_ID":"3000"})
from collector import API, connect, number

TARGET = "2026-10-01"
MAX_PAGES = 20
RESERVE = 100
key = os.environ["SOLDCOMPS_API_KEY"]
session = requests.Session()
headers = {"Authorization":f"Bearer {key}", "X-Credit-Source":"subscription-only"}
db = connect()
db.execute("INSERT OR IGNORE INTO categories(category_id,name) VALUES (?,?)",("20667","Piccoli elettrodomestici per la cucina"))
db.commit()
inserted = seen = calls = 0
try:
    for page in range(1, MAX_PAGES + 1):
        usage = session.get("https://api.sold-comps.com/usage", headers={"Authorization":f"Bearer {key}"},timeout=15)
        usage.raise_for_status()
        remaining = int(usage.json()["usage"]["remaining"])
        if remaining <= RESERVE:
            print(f"STOP: quota {remaining}, riserva {RESERVE}",flush=True)
            break
        params = {"categoryId":"20667","ebaySite":"ebay.it","page":page,"count":240,
                  "sortOrder":"endedRecently","minPrice":100,"conditionId":3000}
        r = session.get(API,params=params,headers=headers,timeout=70)
        if r.status_code == 429:
            print("STOP: quota API esaurita (429)",flush=True)
            break
        r.raise_for_status()
        calls += 1
        payload = r.json()
        items = payload.get("items",[])
        seen += len(items)
        dates = []
        for item in items:
            dt = str(item.get("endedAt") or "")[:10]
            if dt:
                dates.append(dt)
            if not dt or dt < TARGET:
                continue
            price = number(item.get("soldPrice"))
            item_id = str(item.get("itemId") or "")
            if not item_id or price is None or price < 100:
                continue
            now = datetime.now(timezone.utc).isoformat()
            row = db.execute("""INSERT OR IGNORE INTO sales
            (site,item_id,title,url,image,ended_at,sold_price,currency,shipping_price,total_price,
             condition,seller,buying_format,best_offer_accepted,scraped_at,first_seen,category_id)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
             ("ebay.it",item_id,item.get("title"),item.get("url"),item.get("thumbnailUrl"),
              item.get("endedAt"),price,item.get("soldCurrency"),number(item.get("shippingPrice")),
              number(item.get("totalPrice")),item.get("condition"),item.get("sellerUsername"),
              item.get("buyingFormat"),int(bool(item.get("bestOfferAccepted"))),
              item.get("scrapedAt"),now,"20667"))
            inserted += row.rowcount
        db.commit()
        print(f"Pagina {page}: {len(items)} annunci, più vecchio={min(dates) if dates else 'N/D'}, nuovi totali={inserted}, quota precedente={remaining}",flush=True)
        if dates and min(dates) <= TARGET:
            print("Raggiunto il 1 ottobre: stop.",flush=True)
            break
        if not payload.get("hasNextPage") or not items:
            print("Nessun'altra pagina disponibile.",flush=True)
            break
        time.sleep(3)
finally:
    print(f"RISULTATO: {calls} richieste, {seen} annunci esaminati, {inserted} nuovi salvati.",flush=True)
    db.close()
