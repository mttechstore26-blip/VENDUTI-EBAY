"""One-off used consoles historical recovery, October 1-19 2026.
Uses only subscription credits; does not affect systemd schedule.
"""
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
os.environ.update({"EBAY_CATEGORY_ID":"139971","EBAY_CATEGORY_NAME":"CONSOLE 400+",
                   "MIN_PRICE":"400","EBAY_CONDITION_ID":"3000"})
from collector import API, connect, number

SINCE, THROUGH = "2026-10-01", "2026-10-19"
MAX_PAGES, RESERVE = 20, 100
key = os.environ["SOLDCOMPS_API_KEY"]
headers = {"Authorization": f"Bearer {key}", "X-Credit-Source": "subscription-only"}
session = requests.Session()
db = connect()
db.execute("INSERT INTO categories(category_id,name) VALUES (?,?) ON CONFLICT(category_id) DO UPDATE SET name=excluded.name",
           ("139971","CONSOLE 400+"))
db.commit()
inserted = scanned = calls = 0
try:
    for page in range(1, MAX_PAGES + 1):
        usage = session.get("https://api.sold-comps.com/usage",
                            headers={"Authorization": f"Bearer {key}"},timeout=15)
        usage.raise_for_status()
        remaining = int(usage.json()["usage"]["remaining"])
        if remaining <= RESERVE:
            print(f"STOP quota: {remaining}, riserva {RESERVE}",flush=True)
            break
        params={"categoryId":"139971","ebaySite":"ebay.it","page":page,
                "count":240,"sortOrder":"endedRecently","minPrice":400,"conditionId":3000}
        response = session.get(API,params=params,headers=headers,timeout=70)
        if response.status_code == 429:
            print("STOP: quota 429",flush=True)
            break
        response.raise_for_status()
        calls += 1
        data=response.json()
        items=data.get("items",[])
        scanned += len(items)
        dates=[]
        saved_this_page=0
        for item in items:
            day=str(item.get("endedAt") or "")[:10]
            if day: dates.append(day)
            if not (SINCE <= day <= THROUGH): continue
            price=number(item.get("soldPrice"))
            if price is None or not price >= 400: continue
            item_id=str(item.get("itemId") or "")
            if not item_id: continue
            now=datetime.now(timezone.utc).isoformat()
            # Existing eBay ID from another monitored category is not duplicated.
            cur=db.execute("""INSERT OR IGNORE INTO sales
                (site,item_id,title,url,image,ended_at,sold_price,currency,shipping_price,total_price,
                 condition,seller,buying_format,best_offer_accepted,scraped_at,first_seen,category_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("ebay.it",item_id,item.get("title"),item.get("url"),item.get("thumbnailUrl"),
                 item.get("endedAt"),price,item.get("soldCurrency"),number(item.get("shippingPrice")),
                 number(item.get("totalPrice")),item.get("condition"),item.get("sellerUsername"),
                 item.get("buyingFormat"),int(bool(item.get("bestOfferAccepted"))),
                 item.get("scrapedAt"),now,"139971"))
            saved_this_page += cur.rowcount
        db.commit()
        inserted += saved_this_page
        print(f"Pagina {page}: {len(items)} annunci, date {min(dates) if dates else 'N/D'} -> {max(dates) if dates else 'N/D'}, nuovi {saved_this_page}, totale nuovi {inserted}, quota precedente {remaining}",flush=True)
        # A single old outlier does not establish that all October sales have been seen.
        if dates and max(dates) < SINCE:
            print("STOP: intera pagina anteriore al 1 ottobre.",flush=True)
            break
        if not data.get("hasNextPage") or not items:
            print("STOP: nessuna pagina successiva.",flush=True)
            break
        time.sleep(3)
except KeyboardInterrupt:
    print("Interruzione manuale: venduti delle pagine completate già salvati.",flush=True)
finally:
    print(f"RISULTATO: {calls} richieste, {scanned} annunci esaminati, {inserted} nuovi salvati.",flush=True)
    db.close()
