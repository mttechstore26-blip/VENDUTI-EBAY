"""Reset only the Apple 111422 monitor before rebuilding Sep-Oct 150-300 EUR history.

Backs up the SQLite database first. Never touches other categories.
Run backfill_apple_111422_sep2026.py immediately afterwards.
"""
from datetime import datetime
from pathlib import Path
import sqlite3
from backfill_apple_111422_sep2026 import ROOT, STATE, CATEGORY_ID, CATEGORY_NAME

DB = ROOT / "data" / "ebay_sold.db"

def main():
    if not DB.is_file():
        raise SystemExit(f"Database non trovato: {DB}")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = DB.with_name(f"ebay_sold.before_apple_reset_{stamp}.db")
    with sqlite3.connect(DB, timeout=30) as db:
        with sqlite3.connect(backup_path) as backup:
            db.backup(backup)
        before = db.execute("SELECT COUNT(*) FROM sales WHERE category_id=?", (CATEGORY_ID,)).fetchone()[0]
        db.execute("DELETE FROM sales WHERE category_id=?", (CATEGORY_ID,))
        db.execute(
            "INSERT INTO categories(category_id,name) VALUES (?,?) "
            "ON CONFLICT(category_id) DO UPDATE SET name=excluded.name",
            (CATEGORY_ID, CATEGORY_NAME),
        )
        db.commit()
    if STATE.exists():
        STATE.unlink()
    print(f"Backup: {backup_path}")
    print(f"Eliminati {before} annunci SOLO dalla categoria {CATEGORY_ID}; stato backfill azzerato.")
    print("Ora esegui: .venv/bin/python backfill_apple_111422_sep2026.py")

if __name__ == "__main__":
    main()
