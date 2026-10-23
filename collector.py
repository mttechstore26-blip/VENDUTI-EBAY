"""SoldComps category monitoring; intentionally no eBay credentials/cookies."""
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
from dotenv import load_dotenv
from eu_locations import is_eu_location

load_dotenv()
API = 'https://api.sold-comps.com/v1/scrape/category'
DB = Path(os.getenv('DB_PATH', './data/ebay_sold.db'))


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS sales (
        site TEXT NOT NULL, item_id TEXT NOT NULL, title TEXT, url TEXT,
        image TEXT, ended_at TEXT, sold_price REAL, currency TEXT,
        shipping_price REAL, total_price REAL, condition TEXT,
        seller TEXT, buying_format TEXT, best_offer_accepted INTEGER,
        scraped_at TEXT, first_seen TEXT NOT NULL, category_id TEXT,
        PRIMARY KEY(site, item_id)
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ran_at TEXT, items_seen INTEGER,
        inserted INTEGER, status TEXT, message TEXT
    )''')
    cols = {r[1] for r in conn.execute('PRAGMA table_info(sales)')}
    if 'item_location' not in cols:
        conn.execute('ALTER TABLE sales ADD COLUMN item_location TEXT')
    if 'category_id' not in cols:
        conn.execute('ALTER TABLE sales ADD COLUMN category_id TEXT')
    conn.execute('CREATE TABLE IF NOT EXISTS categories (category_id TEXT PRIMARY KEY, name TEXT NOT NULL)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ebay_cat_date ON sales(category_id,ended_at DESC)')
    conn.commit()
    return conn


def number(value):
    try:
        return float(value) if value not in (None, '') else None
    except (ValueError, TypeError):
        return None


def notify(item):
    token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    chat = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    if not (token and chat):
        return
    from html import escape
    title = escape((item.get('title') or 'Senza titolo')[:250])
    price = escape(str(item.get('soldPrice') or '?'))
    currency = escape(str(item.get('soldCurrency') or ''))
    url = item.get('url') or ''
    message = f'🟢 <b>Venduto eBay</b>\n{title}\n<b>{price} {currency}</b>\n{escape(url)}'
    try:
        r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': True}, timeout=15)
        r.raise_for_status()
    except requests.RequestException as exc:
        print(f'Telegram error: {exc}')


def fetch_page(page):
    key = os.getenv('SOLDCOMPS_API_KEY', '').strip()
    if not key or key == 'sc_INSERISCI_QUI':
        raise RuntimeError('Configura SOLDCOMPS_API_KEY nel file .env')
    args = {'categoryId': os.getenv('EBAY_CATEGORY_ID', '141755'),
            'ebaySite': os.getenv('EBAY_SITE', 'ebay.it'),
            'page': page, 'count': int(os.getenv('COUNT_PER_PAGE', '240')),
            'sortOrder': 'endedRecently',
            'minPrice': float(os.getenv('MIN_PRICE', '70'))}
    if os.getenv('EBAY_ITEM_LOCATION', '').strip():
        args['itemLocation'] = os.getenv('EBAY_ITEM_LOCATION').strip()
    if os.getenv('MAX_PRICE', '').strip():
        args['maxPrice'] = float(os.getenv('MAX_PRICE'))
    if os.getenv('EBAY_CONDITION_ID', '').strip():
        args['conditionId'] = int(os.getenv('EBAY_CONDITION_ID'))
    r = requests.get(API, params=args, headers={'Authorization': f'Bearer {key}',
        'X-Credit-Source': 'subscription-only'}, timeout=70)
    if r.status_code == 429:
        raise RuntimeError('Limite API raggiunto (429): raccolta interrotta, nessun credito extra utilizzato')
    r.raise_for_status()
    return r.json()


def run():
    conn = connect()
    category_id = os.getenv('EBAY_CATEGORY_ID', '141755')
    # Apple monitor may overlap another laptop category; isolate its SQLite PK.
    site = os.getenv('EBAY_SITE', 'ebay.it') + (':111422' if category_id == '111422' else '')
    category_name = os.getenv('EBAY_CATEGORY_NAME', 'Album di figurine' if category_id=='141755' else 'Categoria '+category_id)
    conn.execute('INSERT INTO categories(category_id,name) VALUES (?,?) ON CONFLICT(category_id) DO UPDATE SET name=excluded.name', (category_id,category_name))
    conn.commit()
    baseline_exists = conn.execute('SELECT 1 FROM sales WHERE category_id=? LIMIT 1', (category_id,)).fetchone() is not None
    items_seen = inserted = 0
    status, message = 'ok', ''
    try:
        max_pages = max(1, min(100, int(os.getenv('MAX_PAGES_PER_RUN', '1'))))
        for page in range(1, max_pages + 1):
            payload = fetch_page(page)
            items = payload.get('items', [])
            items_seen += len(items)
            for item in items:
                if category_id in ('139971', '171485') and not is_eu_location(item.get('itemLocation')):
                    continue
                price = number(item.get('soldPrice'))
                if price is None or price < float(os.getenv('MIN_PRICE', '70')):
                    continue
                if os.getenv('MAX_PRICE', '').strip() and price > float(os.getenv('MAX_PRICE')):
                    continue
                item_id = str(item.get('itemId') or '')
                if not item_id:
                    continue
                now = datetime.now(timezone.utc).isoformat()
                cur = conn.execute('''INSERT OR IGNORE INTO sales
                    (site,item_id,title,url,image,ended_at,sold_price,currency,shipping_price,total_price,
                    condition,seller,buying_format,best_offer_accepted,scraped_at,first_seen,category_id,item_location)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (site,item_id,item.get('title'),item.get('url'),item.get('thumbnailUrl'),
                    item.get('endedAt'),number(item.get('soldPrice')),item.get('soldCurrency'),
                    number(item.get('shippingPrice')),number(item.get('totalPrice')),item.get('condition'),
                    item.get('sellerUsername'),item.get('buyingFormat'),
                    int(bool(item.get('bestOfferAccepted'))),item.get('scrapedAt'),now,category_id,
                    str(item.get('itemLocation') or '')))
                if cur.rowcount:
                    inserted += 1
                    # The initial ingestion is a baseline; do not flood Telegram with historical data.
                    if baseline_exists:
                        notify(item)
            # Restore the optional location for existing IDs without duplicating sales.
            for item in items:
                loc = item.get('itemLocation')
                if loc and item.get('itemId'):
                    conn.execute('UPDATE sales SET item_location=? WHERE site=? AND item_id=? AND (item_location IS NULL OR item_location=\'\')',
                                 (str(loc), site, str(item.get('itemId'))))
            conn.commit()
            if not payload.get('hasNextPage'):
                break
            if page < max_pages:
                time.sleep(3)
    except Exception as exc:
        status, message = 'error', str(exc)
        print('ERROR:', message)
    finally:
        conn.execute('INSERT INTO runs (ran_at,items_seen,inserted,status,message) VALUES (?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(),items_seen,inserted,status,message))
        conn.commit()
        conn.close()
    print(f'{status}: items={items_seen}; nuovi={inserted}; {message}')
    return status == 'ok'

if __name__ == '__main__':
    raise SystemExit(0 if run() else 1)
