"""Dedicated SoldComps monitor for eBay Italia category 20667.
No keyword or max-price filter. Keeps the existing category monitor intact.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')
os.environ.update({
    'EBAY_SITE': 'ebay.it',
    'EBAY_CATEGORY_ID': '20667',
    'EBAY_CATEGORY_NAME': 'Piccoli elettrodomestici per la cucina',
    'MIN_PRICE': '100',
    'EBAY_CONDITION_ID': '3000',
})
# Existing collector doesn't send maxPrice; all prices >= 100 EUR are included.
from collector import run

if __name__ == '__main__':
    raise SystemExit(0 if run() else 1)
