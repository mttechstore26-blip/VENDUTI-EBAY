"""Optional Discord notifications for newly sold watched or high-volume models.
Runs locally after a successful SoldComps collection. No extra API quota.
Set DISCORD_WEBHOOK_URL in VPS .env; never commit it.
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone
import requests
from dotenv import load_dotenv
from eu_locations import is_eu_location

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DB = (ROOT / os.getenv("DB_PATH", "./data/ebay_sold.db")).resolve()
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

def classify_model(category, title):
    from ebay_taxonomy import classify
    from kitchen_taxonomy import classify_kitchen
    from coffee_taxonomy import classify_coffee
    from console_taxonomy import classify_console
    from apple_laptop_taxonomy import classify_apple_laptop
    from laptop_taxonomy import classify_laptop
    from monitor_taxonomy import classify_monitor
    functions = {
        "20667": classify_kitchen, "38250": classify_coffee,
        "139971": classify_console, "111422": classify_apple_laptop,
        "175672": classify_laptop, "80053": classify_monitor
    }
    try:
        result = functions[str(category)](title) if str(category) in functions else classify(str(category), title)
        brand, family, model = result[:3]
        model = str(model or "").strip()
        family = str(family or "").strip()
        if not model or any(word in model.casefold() for word in
                ("da identificare", "non identificato", "non specificato", "da verificare")):
            model = family
        return model or None
    except Exception:
        return None

def run():
    if not WEBHOOK:
        print("[DISCORD] webhook non configurato: notifiche disabilitate")
        return
    if not WEBHOOK.startswith(("https://discord.com/api/webhooks/", "https://discordapp.com/api/webhooks/")):
        print("[DISCORD] URL webhook non valido")
        return
    with sqlite3.connect(DB, timeout=20) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS discord_alert_state (
            category_id TEXT NOT NULL, model_name TEXT NOT NULL,
            last_sale_id TEXT, last_volume_alert_at TEXT,
            PRIMARY KEY(category_id,model_name))""")
        db.execute("""CREATE TABLE IF NOT EXISTS discord_alert_meta (
            key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
        # The first execution creates a baseline, never notifies historical sales.
        ready = db.execute("SELECT value FROM discord_alert_meta WHERE key='initialized'").fetchone()
        if not ready:
            db.execute("INSERT INTO discord_alert_meta(key,value) VALUES('initialized',?)",
                       (datetime.now(timezone.utc).isoformat(),))
            print("[DISCORD] baseline inizializzata; nessuna notifica storica")
            return
        since = datetime.now(timezone.utc) - timedelta(days=7)
        data = db.execute("""SELECT category_id,item_id,title,sold_price,ended_at,first_seen,item_location
                             FROM sales WHERE ended_at>=? AND sold_price>=70
                             ORDER BY ended_at DESC""", (since.isoformat(),)).fetchall()
        watched = set()
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='model_watchlist'").fetchone():
            watched = {(str(c),str(m)) for c,m in db.execute(
                "SELECT category_id,model_name FROM model_watchlist")}
        grouped = {}
        for cat, sid, title, price, ended, first_seen, location in data:
            if (str(cat) == '139971' and (float(price or 0) < 300 or not is_eu_location(location))) or (str(cat) == '171485' and (not 100 <= float(price or 0) <= 250 or not is_eu_location(location))):
                continue
            model = classify_model(cat, title or "")
            if not model:
                continue
            grouped.setdefault((str(cat),model), []).append((str(sid),float(price or 0), first_seen))
        for (cat,model), entries in sorted(grouped.items()):
            entries.sort(key=lambda x: x[2] or "", reverse=True)
            count = len(entries)
            latest_id, _, first_seen = entries[0]
            prior = db.execute("SELECT last_sale_id,last_volume_alert_at FROM discord_alert_state WHERE category_id=? AND model_name=?", (cat,model)).fetchone()
            is_watched = (cat,model) in watched
            last_sale = prior[0] if prior else None
            last_volume = prior[1] if prior else None
            # For watchlist: only if new sale arrived since last successful alert.
            # For high volume: notify at most once per 7 days per model.
            new_sale = bool(first_seen and first_seen > ready[0] and latest_id != last_sale)
            cooldown_ok = not last_volume or (datetime.now(timezone.utc) - datetime.fromisoformat(last_volume)).total_seconds() >= 7*86400
            alert_watch = is_watched and new_sale
            alert_volume = count >= 5 and cooldown_ok and new_sale
            if not (alert_watch or alert_volume):
                continue
            prices = sorted(p for _,p,_ in entries if p > 0)
            median = prices[len(prices)//2] if len(prices)%2 else (prices[len(prices)//2-1]+prices[len(prices)//2])/2
            affordable = []
            for minimum,maximum,margin in ((10,50,25),(51,100,30),(101,float('inf'),40)):
                candidate = min(maximum,median-margin)
                if candidate >= minimum:
                    affordable.append(candidate)
            max_buy = max(affordable) if affordable else None
            body = (
                f"🔥 **{model}**\\nCategoria eBay: {cat}\\n"
                f"Venduti ultimi 7 giorni: **{count}**\\n"
                f"Prezzo mediano: **€{median:.2f}**\\n"
                f"Acquisto massimo consigliato: **€{max_buy:.2f}**"
                if max_buy is not None else
                f"🔥 **{model}**\\nCategoria eBay: {cat}\\nVenduti ultimi 7 giorni: **{count}**\\n"
                f"Prezzo mediano: **€{median:.2f}**\\nAcquisto non conveniente alle soglie impostate"
            )
            body = body.replace("\\n","\n")
            try:
                response = requests.post(WEBHOOK,json={"content":body[:1900],
                    "allowed_mentions":{"parse":[]}},timeout=12)
                response.raise_for_status()
            except requests.RequestException as exc:
                print("[DISCORD] invio fallito:",type(exc).__name__)
                continue
            db.execute("""INSERT INTO discord_alert_state(category_id,model_name,last_sale_id,last_volume_alert_at)
                VALUES(?,?,?,?) ON CONFLICT(category_id,model_name) DO UPDATE SET
                last_sale_id=excluded.last_sale_id,
                last_volume_alert_at=COALESCE(excluded.last_volume_alert_at,discord_alert_state.last_volume_alert_at)""",
                (cat,model,latest_id,datetime.now(timezone.utc).isoformat() if alert_volume else None))
            db.commit()
            print("[DISCORD] notificato",cat,model)

if __name__ == "__main__":
    run()
