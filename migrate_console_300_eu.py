"""One-time reversible cleanup of console sales for the EU-only 300+ monitor.

Run on the VPS after deploying the updated code. The backup is a full SQLite
snapshot and excluded rows are also copied into a separate archive table.
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from eu_locations import is_eu_location

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DB = (ROOT / os.getenv("DB_PATH", "./data/ebay_sold.db")).resolve()

def main():
    if not DB.is_file():
        raise SystemExit("Database non trovato")
    backup_path = DB.with_name(DB.name + ".before_console300_eu")
    with sqlite3.connect(DB, timeout=30) as db:
        db.create_function("is_eu_location", 1, lambda x: int(is_eu_location(x)))
        if not backup_path.exists():
            with sqlite3.connect(backup_path) as backup:
                db.backup(backup)
            print("Backup SQLite completo:", backup_path)
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS console_300_eu_excluded AS
            SELECT *, '' AS archived_at FROM sales WHERE 0""")
        filter_sql = """category_id='139971'
            AND (sold_price IS NULL OR sold_price<300
                 OR is_eu_location(item_location)=0)"""
        count = db.execute("SELECT COUNT(*) FROM sales WHERE " + filter_sql).fetchone()[0]
        stamp = datetime.now(timezone.utc).isoformat()
        db.execute("""INSERT INTO console_300_eu_excluded
            SELECT *, ? FROM sales WHERE """ + filter_sql, (stamp,))
        db.execute("DELETE FROM sales WHERE " + filter_sql)
        db.execute("""INSERT INTO categories(category_id,name) VALUES('139971','CONSOLE 300+ 🇪🇺')
            ON CONFLICT(category_id) DO UPDATE SET name=excluded.name""")
        db.commit()
        remaining = db.execute("""SELECT COUNT(*) FROM sales
            WHERE category_id='139971'""").fetchone()[0]
        print(f"Archiviati {count} annunci console fuori criteri; visibili {remaining}.")
        print("Gli annunci senza località esplicita sono archiviati, non attribuiti all'UE.")
        print("Ripristino possibile dal backup:", backup_path)

if __name__ == "__main__":
    main()
