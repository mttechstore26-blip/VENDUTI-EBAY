"""Historical Monitor 80053 backfill, safely one API page per invocation.
Run repeatedly until it reports COMPLETE. Keeps regular collector unchanged.
"""
import os, sqlite3, sys
from datetime import datetime, timezone, date
from pathlib import Path
import requests
from dotenv import load_dotenv
from collector import connect, number, API

ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
CUTOFF='2026-09-01'
CATEGORY='80053'
STATE=ROOT/'data/monitor_80053_backfill.state'
RESERVE=10

def main():
    if STATE.exists():
        value=STATE.read_text().strip()
        if value=='COMPLETE':
            print('COMPLETE: storico già raggiunto al 1 settembre');return
        page=int(value)
    else:
        page=1
    key=os.getenv('SOLDCOMPS_API_KEY','').strip()
    if not key:sys.exit('API key missing')
    try:
        usage=requests.get('https://api.sold-comps.com/usage',headers={'Authorization':f'Bearer {key}'},timeout=(5,12))
        usage.raise_for_status()
        remaining=int(usage.json()['usage']['remaining'])
    except (requests.RequestException,KeyError,TypeError,ValueError) as e:
        sys.exit('Quota non verificabile, nessuna richiesta effettuata: '+str(e))
    if remaining<=RESERVE:
        print(f'STOP: solo {remaining} crediti, riserva {RESERVE}');return
    params={'categoryId':CATEGORY,'ebaySite':'ebay.it','page':page,'count':240,
            'sortOrder':'endedRecently','minPrice':100,'maxPrice':300,
            'conditionId':3000,'itemLocation':'domestic'}
    try:
        r=requests.get(API,params=params,headers={'Authorization':f'Bearer {key}',
                         'X-Credit-Source':'subscription-only'},timeout=70)
        if r.status_code==429:
            print('Quota API esaurita, nessuna ulteriore richiesta');return
        r.raise_for_status()
        payload=r.json()
    except (requests.RequestException, ValueError) as e:
        sys.exit('Richiesta non riuscita, pagina non avanzata: '+str(e))
    items=payload.get('items',[])
    conn=connect()
    conn.execute("INSERT INTO categories(category_id,name) VALUES (?,?) ON CONFLICT(category_id) DO UPDATE SET name=excluded.name",
                (CATEGORY,'Monitor usati Italia 100-300'))
    added=0; older=False; dates_known=0
    for item in items:
        ended=str(item.get('endedAt') or '')
        if not ended:
            continue
        dates_known+=1
        if ended[:10]<CUTOFF:
            older=True
            continue
        price=number(item.get('soldPrice'))
        if price is None or price<100 or price>300:continue
        item_id=str(item.get('itemId') or '')
        if not item_id:continue
        now=datetime.now(timezone.utc).isoformat()
        cur=conn.execute("""INSERT OR IGNORE INTO sales
          (site,item_id,title,url,image,ended_at,sold_price,currency,shipping_price,total_price,
           condition,seller,buying_format,best_offer_accepted,scraped_at,first_seen,category_id,item_location)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          ('ebay.it',item_id,item.get('title'),item.get('url'),item.get('thumbnailUrl'),
           item.get('endedAt'),price,item.get('soldCurrency'),
           number(item.get('shippingPrice')),number(item.get('totalPrice')),item.get('condition'),
           item.get('sellerUsername'),item.get('buyingFormat'),
           int(bool(item.get('bestOfferAccepted'))),item.get('scrapedAt'),now,CATEGORY,
           str(item.get('itemLocation') or '')))
        added+=int(cur.rowcount>0)
    conn.commit();conn.close()
    complete=older or not payload.get('hasNextPage',False) or not items
    if dates_known==0 and items:
        print('ATTENZIONE: date vendite assenti; pagina non avanzata')
        return
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text('COMPLETE' if complete else str(page+1))
    print(f'Pagina {page}: {len(items)} annunci, {added} inseriti; '
          f'stato={"COMPLETE" if complete else "prossima pagina "+str(page+1)}; '
          f'credito stimato residuo prima della richiesta={remaining}')
if __name__=='__main__':
    main()
