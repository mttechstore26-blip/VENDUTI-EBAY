"""One-time backward-compatible category migration. No API calls."""
from pathlib import Path
import sqlite3, os
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
DB=(ROOT/os.getenv('DB_PATH','./data/ebay_sold.db')).resolve()
assert DB.exists(), f'Database not found: {DB}'
conn=sqlite3.connect(DB)
try:
    conn.execute('BEGIN IMMEDIATE')
    columns={row[1] for row in conn.execute('PRAGMA table_info(sales)')}
    if 'category_id' not in columns:
        conn.execute('ALTER TABLE sales ADD COLUMN category_id TEXT')
    conn.execute('CREATE TABLE IF NOT EXISTS categories (category_id TEXT PRIMARY KEY, name TEXT NOT NULL)')
    conn.execute('INSERT OR IGNORE INTO categories(category_id,name) VALUES (?,?)', ('141755','Album di figurine'))
    conn.execute("UPDATE sales SET category_id='141755' WHERE category_id IS NULL OR category_id = ''")
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ebay_cat_date ON sales(category_id, ended_at DESC)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_ebay_cat_price ON sales(category_id, sold_price)')
    conn.commit()
    print('OK: record categoria 141755:', conn.execute("SELECT COUNT(*) FROM sales WHERE category_id='141755'").fetchone()[0])
finally:
    conn.close()
