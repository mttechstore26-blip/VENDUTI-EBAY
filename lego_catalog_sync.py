"""Conservative official LEGO Italy catalog refresh; no SoldComps calls."""
import os, re, sqlite3, time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, quote
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
DB=(ROOT/os.getenv('DB_PATH','./data/ebay_sold.db')).resolve()
CAT=(ROOT/'data/lego_catalog.db').resolve()
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; LEGO-catalog-maintenance/1.0)'}
SEEDS={
 '76294':('X-Men: X-Mansion','https://www.lego.com/it-it/product/x-men-the-x-mansion-76294'),
 '21325':('Fabbro medievale','https://www.lego.com/it-it/product/medieval-blacksmith-21325'),
}
def setup(db):
 db.execute('''CREATE TABLE IF NOT EXISTS lego_catalog (
 code TEXT PRIMARY KEY, name TEXT, status TEXT NOT NULL DEFAULT 'da verificare',
 official_url TEXT, checked_at TEXT, source TEXT NOT NULL DEFAULT 'LEGO Italia')''')
 db.commit()
def candidates():
 with sqlite3.connect(f'file:{DB}?mode=ro',uri=True) as db:
  titles=db.execute("SELECT title FROM sales WHERE category_id='183446' AND title IS NOT NULL").fetchall()
 counts={}
 for (title,) in titles:
  t=title.casefold()
  if not re.search(r'\blego\b',t):continue
  for m in re.finditer(r'(?<![a-z0-9])(\d{4,6})(?![a-z0-9])',t):
   code=m.group(1)
   if 1900<=int(code)<=2099:continue
   if re.match(r'\s*(?:pezzi|pz|pieces|pcs|parts)\b',t[m.end():]):continue
   counts[code]=counts.get(code,0)+1
 return sorted(counts,key=lambda c:(-counts[c],c))
def official(url,code):
 parsed=urlparse(url)
 if parsed.scheme!='https' or parsed.hostname not in ('www.lego.com','lego.com') or not parsed.path.startswith('/it-it/product/'):
  return None
 if not parsed.path.rstrip('/').endswith('-'+code):return None
 try:
  r=requests.get(url,headers=HEADERS,timeout=20,allow_redirects=True)
  r.raise_for_status()
  if urlparse(r.url).hostname not in ('www.lego.com','lego.com'):return None
  soup=BeautifulSoup(r.text,'html.parser')
  txt=soup.get_text(' ',strip=True)
  if not re.search(r'(?<!\d)'+re.escape(code)+r'(?!\d)',txt):return None
  h=soup.find('h1')
  name=h.get_text(' ',strip=True) if h else None
  if not name:return None
  if re.search(r'\bprodotto ritirato\b',txt,re.I):status='ritirato'
  elif re.search(r'\bdisponibile ora\b',txt,re.I) and re.search(r'aggiungi al carrello',txt,re.I):status='disponibile'
  else:status='da verificare'
  return name,status,r.url
 except requests.RequestException:
  return None
def search_url(code):
 # Discovery is only a candidate link; never treat search snippets as product evidence.
 url='https://www.lego.com/it-it/search?q='+quote(code)
 try:
  r=requests.get(url,headers=HEADERS,timeout=20)
  r.raise_for_status()
  soup=BeautifulSoup(r.text,'html.parser')
  links=[]
  for a in soup.select('a[href]'):
   href=urljoin(r.url,a['href'])
   p=urlparse(href)
   if p.hostname in ('www.lego.com','lego.com') and p.path.startswith('/it-it/product/') and p.path.rstrip('/').endswith('-'+code):
    links.append(href.split('?')[0])
  return links[0] if links else None
 except requests.RequestException:return None
def main():
 if not DB.exists():raise SystemExit('Sales database missing')
 CAT.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(CAT) as db:
  setup(db)
  for code,(name,url) in SEEDS.items():
   db.execute('INSERT OR IGNORE INTO lego_catalog(code,name,official_url) VALUES (?,?,?)',(code,name,url))
  db.commit()
  codes=candidates()
  for code in codes[:250]:
   db.execute("INSERT OR IGNORE INTO lego_catalog(code) VALUES (?)",(code,))
  db.commit()
  rows=db.execute("SELECT code,official_url,checked_at FROM lego_catalog ORDER BY CASE WHEN checked_at IS NULL THEN 0 ELSE 1 END,checked_at LIMIT 35").fetchall()
  for code,url,last in rows:
   target=url or search_url(code)
   result=official(target,code) if target else None
   # Preserve last confirmed state if a network failure occurs; never infer 'retired'.
   if result:
    name,state,source=result
    db.execute("UPDATE lego_catalog SET name=?,status=?,official_url=?,checked_at=? WHERE code=?",
               (name,state,source,datetime.now(timezone.utc).isoformat(),code))
   else:
    db.execute("UPDATE lego_catalog SET checked_at=? WHERE code=?",(datetime.now(timezone.utc).isoformat(),code))
   db.commit()
   time.sleep(1)
  print('Catalog total:',db.execute('SELECT COUNT(*) FROM lego_catalog').fetchone()[0])
if __name__=='__main__':main()
