"""Diagnose SoldComps category 111422 filtering; read-only, one paid category request.

Reports the actual returned price/date/condition/location distribution.
Does not change the SQLite database or store private credentials.
"""
import collections
import os
import requests
from dotenv import load_dotenv

from collector import API, number

load_dotenv()
key = os.getenv("SOLDCOMPS_API_KEY", "").strip()
if not key:
    raise SystemExit("Chiave SoldComps assente")

headers = {"Authorization": f"Bearer {key}"}
usage = requests.get("https://api.sold-comps.com/usage", headers=headers, timeout=(5, 12))
usage.raise_for_status()
remaining = int(usage.json()["usage"]["remaining"])
if remaining <= 10:
    raise SystemExit(f"Quota troppo bassa: {remaining}; nessuna ricerca effettuata")

params = {
    "categoryId": "111422", "ebaySite": "ebay.it", "page": 1, "count": 240,
    "sortOrder": "endedRecently", "minPrice": 150, "maxPrice": 300,
    "conditionId": 3000, "itemLocation": "domestic",
}
response = requests.get(
    API, params=params,
    headers={**headers, "X-Credit-Source": "subscription-only"}, timeout=70,
)
if response.status_code == 429:
    raise SystemExit("API 429: interrompo senza costi extra")
response.raise_for_status()
payload = response.json()
items = payload.get("items", [])
if not isinstance(items, list):
    raise SystemExit("Risposta inattesa: items non è una lista")

prices = collections.Counter()
dates = collections.Counter()
conditions = collections.Counter()
locations = collections.Counter()
samples = []
matched = 0
for item in items:
    p = number(item.get("soldPrice"))
    day = str(item.get("endedAt") or "")[:10]
    cond = str(item.get("condition") or "<vuoto>")
    loc = str(item.get("itemLocation") or "<vuoto>")
    conditions[cond] += 1
    locations[loc] += 1
    if p is None:
        prices["Prezzo assente"] += 1
    elif p < 150:
        prices["Sotto 150"] += 1
    elif p <= 300:
        prices["150-300"] += 1
    else:
        prices["Oltre 300"] += 1
    if not day:
        dates["Data assente"] += 1
    elif day < "2026-09-01":
        dates["Prima del 1 settembre"] += 1
    elif day <= "2026-10-21":
        dates["1 settembre - 21 ottobre"] += 1
    else:
        dates["Dopo il 21 ottobre"] += 1
    if p is not None and 150 <= p <= 300 and "2026-09-01" <= day <= "2026-10-21":
        matched += 1
    if len(samples) < 8:
        samples.append((str(item.get("title") or "")[:65], p, day, cond, loc))

print(f"Totale API: {len(items)} | hasNextPage: {payload.get('hasNextPage')} | quota prima: {remaining}")
print("Prezzi:", dict(prices))
print("Date:", dict(dates))
print("Condizioni:", dict(conditions))
print("Provenienza:", dict(locations.most_common(12)))
print("Validi per prezzo e periodo:", matched)
print("Primi 8 risultati (titolo, prezzo, data, condizione, provenienza):")
for row in samples:
    print(row)
