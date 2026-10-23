"""Read-only pilot: inspect up to 10 archived consoles with missing location on eBay.

No SoldComps calls, no database changes. Stop on access restrictions.
"""
import html
import json
import re
import sqlite3
import time
from html.parser import HTMLParser
from pathlib import Path
import os

import requests
from dotenv import load_dotenv
from eu_locations import is_eu_location

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DB = (ROOT / os.getenv("DB_PATH", "./data/ebay_sold.db")).resolve()
MAX_ITEMS = 10

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
    def handle_data(self, value):
        if not self.skip:
            self.parts.append(value)

def location_from_html(source):
    # Item-page shipping panel: extract only the text immediately after its
    # location label, not arbitrary occurrences of country names elsewhere.
    parser = VisibleText()
    parser.feed(source)
    text = " ".join(" ".join(parser.parts).split())
    patterns = [
        r"Oggetto che si trova a\s*:\s*(.{1,110}?)(?=\s*(?:Spedizione|Consegna|Restituzioni|Pagamenti|Dettagli|Vedi i dettagli|\||$))",
        r"Located in\s*:\s*(.{1,110}?)(?=\s*(?:Shipping|Delivery|Returns|Payments|See details|$))",
        r"Artikelstandort\s*:\s*(.{1,110}?)(?=\s*(?:Versand|Lieferung|Rücknahme|$))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1).strip(" ,.;")
    return None

def main():
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("""SELECT item_id, title FROM console_300_eu_excluded
            WHERE item_location IS NULL OR TRIM(item_location)=''
            ORDER BY CASE WHEN item_id='960071387531' THEN 0 ELSE 1 END,
                     ended_at DESC, item_id
            LIMIT ?""", (MAX_ITEMS,)).fetchall()
    if not rows:
        print("Nessun annuncio sconosciuto in archivio")
        return
    session = requests.Session()
    print(f"Campione: {len(rows)} annunci. Solo lettura, nessuna richiesta SoldComps.")
    for index, (item_id, title) in enumerate(rows, 1):
        url = f"https://www.ebay.it/itm/{item_id}"
        try:
            response = session.get(url, timeout=(8, 20), allow_redirects=True,
                                   headers={"Accept-Language": "it-IT,it;q=0.9"})
        except requests.RequestException as exc:
            print(f"{index}. {item_id}: ERRORE RETE ({type(exc).__name__})")
            break
        if response.status_code in (403, 429, 503):
            print(f"{index}. {item_id}: HTTP {response.status_code}; stop, accesso limitato")
            break
        if response.status_code != 200:
            print(f"{index}. {item_id}: HTTP {response.status_code}; non verificato")
            continue
        location = location_from_html(response.text)
        outcome = ("UE" if is_eu_location(location) else
                   "NON VERIFICATA (non inserire automaticamente)")
        print(f"{index}. {item_id}: {outcome}; località={location!r}; "
              f"titolo={str(title or '')[:45]!r}")
        if index < len(rows):
            time.sleep(3)

if __name__ == "__main__":
    main()
