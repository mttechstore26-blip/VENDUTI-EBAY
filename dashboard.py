"""Venduti eBay: fast SQLite-backed Streamlit dashboard, category-wide collection unchanged."""
import os
import sqlite3
from html import escape
from urllib.parse import urlparse
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')
st.set_page_config(page_title='Venduti eBay | MT TECH', page_icon='📚', layout='wide')
DB = (Path(__file__).resolve().parent / os.getenv('DB_PATH', './data/ebay_sold.db')).resolve()

st.markdown('''<style>
.stApp {background:radial-gradient(circle at 8% 0%,#e8efff 0%,transparent 31%),linear-gradient(180deg,#fbfdff,#f0f4fa)}
.block-container {max-width:1500px;padding-top:1.3rem}
h1,h2,h3 {letter-spacing:-.035em;color:#0f172a}
div[data-testid="stMetric"] {background:#ffffffde;border:1px solid #e2e8f0;border-radius:19px;padding:18px 20px;box-shadow:0 9px 27px #0f172a0a}
div[data-testid="stMetric"]:before {content:"";display:block;height:3px;background:linear-gradient(90deg,#2563eb,#7c3aed);margin:-18px -20px 13px;border-radius:19px 19px 0 0}
div[data-testid="stDataFrame"] {border-radius:15px;overflow:hidden}
.mt-hero {padding:25px 29px;color:white;border-radius:24px;background:radial-gradient(circle at 93% 10%,#564cba 0%,transparent 34%),linear-gradient(125deg,#101a33,#1e3566 65%,#312e81);box-shadow:0 15px 35px #0f172a20;margin-bottom:16px}
.mt-title {font-size:30px;font-weight:850;letter-spacing:-1px}.mt-subtitle{color:#cad4e8;font-size:14px;margin-top:6px}

.mt-sale-table{width:100%;border-collapse:separate;border-spacing:0;background:white;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;font-size:13px}
.mt-sale-table th{background:#f1f5f9;color:#475569;font-size:12px;text-align:left;padding:13px 10px;position:sticky;top:0}
.mt-sale-table td{padding:10px;border-top:1px solid #e9edf5;vertical-align:middle;color:#334155}
.mt-sale-table tr:hover td{background:#f8fafc}
.mt-sale-table a{color:#1d4ed8;text-decoration:none;font-weight:650}
.mt-sale-table a:hover{text-decoration:underline}
.mt-sale-table img{width:112px;height:124px;object-fit:contain;border-radius:12px;background:#f8fafc;display:block}
.mt-sale-table .price{font-weight:750;white-space:nowrap}
.mt-scroll{overflow:auto;border-radius:16px}
.mt-sale-table .muted{color:#94a3b8}
@media(max-width:900px){.mt-sale-table{min-width:980px}}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="mt-hero"><div class="mt-title">📚 Venduti eBay</div><div class="mt-subtitle">MT TECH · Analisi per categorie · Raccolta senza parole chiave · Da 70 €</div></div>', unsafe_allow_html=True)

if not DB.is_file():
    st.warning('Database non trovato. Verifica DB_PATH nel file .env.')
    st.stop()

def connect():
    uri = f'file:{DB.as_posix()}?mode=ro'
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.execute('PRAGMA busy_timeout=5000')
    return conn

@st.cache_data(ttl=40, show_spinner=False)
def fetch(sql, params=()):
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)

@st.cache_data(ttl=40, show_spinner=False)
def load_categories():
    return fetch('''SELECT c.category_id, c.name, COUNT(s.item_id) AS n
                    FROM categories c LEFT JOIN sales s ON s.category_id=c.category_id AND s.sold_price>=70
                    GROUP BY c.category_id,c.name ORDER BY c.name''')

if 'category_id' not in [r[1] for r in sqlite3.connect(DB).execute('PRAGMA table_info(sales)').fetchall()]:
    st.error('Database da aggiornare: esegui prima upgrade_categories.py sulla VPS.')
    st.stop()

try:
    category_df=load_categories()
except sqlite3.OperationalError:
    st.error('Tabella categorie mancante: esegui upgrade_categories.py sulla VPS.')
    st.stop()

names={str(r.category_id): f'{r.name} ({int(r.n)} venduti)' for r in category_df.itertuples(index=False)}


with st.sidebar:
    st.header('📂 Navigazione')
    section = st.radio('Sezione', ['📊 Dashboard', '🏷️ Categorie', '📦 Annunci venduti'])
    category_opt = st.selectbox('Categoria', ['Tutte le categorie'] + list(names), format_func=lambda k: names.get(k, k))
    selected_category = None if category_opt == 'Tutte le categorie' else category_opt
    st.divider()
    st.header('🔎 Filtri')
    search = st.text_input('Cerca nel titolo', placeholder='Panini, 1978, Calciatori…', help='Questo filtro agisce solo sulla dashboard, non sulla raccolta eBay.')
    period = st.selectbox('Periodo', ['Tutti', 'Ultimi 7 giorni', 'Ultimi 30 giorni', 'Ultimi 90 giorni', 'Ultimi 365 giorni'])
    condition = st.selectbox('Condizione', ['Tutte', 'Nuovo', 'Di seconda mano'])
    max_df = fetch('SELECT MAX(sold_price) hi FROM sales WHERE sold_price>=70')
    highest = int(max(70, max_df.iloc[0]['hi'] or 70))
    price_low = st.number_input('Prezzo minimo visualizzato (€)', min_value=70, max_value=max(70,highest), value=70, step=10)
    price_high = st.number_input('Prezzo massimo visualizzato (€)', min_value=int(price_low), value=max(highest,int(price_low)), step=20)
    sort = st.selectbox('Ordina', ['Venduti più recenti', 'Prezzo crescente', 'Prezzo decrescente'])
    page_size = st.selectbox('Annunci per pagina', [25, 50, 100], index=1)
    if st.button('↻ Aggiorna dati', width='stretch'):
        fetch.clear()
        load_categories.clear()
        st.rerun()

where = ['sold_price >= ?', 'sold_price >= ?', 'sold_price <= ?']
params = [70, float(price_low), float(price_high)]
if selected_category is not None:
    where.append('category_id = ?')
    params.append(selected_category)
if search.strip():
    where.append('LOWER(COALESCE(title, "")) LIKE ? ESCAPE "\\"')
    escaped = search.lower().strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
    params.append(f'%{escaped}%')
if period != 'Tutti':
    days = {'Ultimi 7 giorni':7,'Ultimi 30 giorni':30,'Ultimi 90 giorni':90,'Ultimi 365 giorni':365}[period]
    where.append("date(ended_at) >= date('now', ?)")
    params.append(f'-{days} days')
if condition != 'Tutte':
    where.append('condition = ?')
    params.append(condition)
where_sql = ' AND '.join(where)
base = ' FROM sales WHERE ' + where_sql
summary = fetch('SELECT COUNT(*) n, ROUND(AVG(sold_price),2) avg_price, MIN(sold_price) low_price, MAX(sold_price) high_price FROM sales WHERE ' + where_sql, tuple(params)).iloc[0]
count = int(summary['n'])
median_rows = fetch('SELECT sold_price FROM sales WHERE ' + where_sql + ' ORDER BY sold_price LIMIT ? OFFSET ?', tuple(params + [2 if count % 2 == 0 else 1, max(0, (count - 1) // 2)])) if count else pd.DataFrame()
median = median_rows['sold_price'].mean() if count else 0

def eur(value):
    return ('€ {:,.2f}'.format(float(value or 0))).replace(',', 'X').replace('.', ',').replace('X', '.')

k1,k2,k3,k4=st.columns(4)
k1.metric('📦 Venduti trovati', f'{count:,}'.replace(',','.'))
k2.metric('📊 Prezzo mediano', eur(median))
k3.metric('💶 Prezzo medio', eur(summary['avg_price']))
k4.metric('🏆 Prezzo più alto', eur(summary['high_price']))

if section == '🏷️ Categorie':
    st.subheader('🏷️ Categorie monitorate')
    st.caption('Le categorie vengono mantenute separate nel database. Puoi aggiungerne altre in futuro senza cambiare la dashboard.')
    totals = fetch('''SELECT c.category_id AS ID, c.name AS Categoria,
                             COUNT(s.item_id) AS Venduti,
                             ROUND(AVG(s.sold_price),2) AS "Prezzo medio €",
                             ROUND(MAX(s.sold_price),2) AS "Prezzo massimo €"
                      FROM categories c LEFT JOIN sales s
                      ON s.category_id=c.category_id AND s.sold_price>=70
                      GROUP BY c.category_id,c.name ORDER BY Venduti DESC''')
    st.dataframe(totals, hide_index=True, width='stretch')
    st.info('Seleziona una categoria nella barra laterale per vedere soltanto le sue vendite.')
else:
    st.subheader('📦 Annunci venduti' if section == '📦 Annunci venduti' else '🕒 Ultimi annunci venduti')
if section != '🏷️ Categorie' and not count:
    st.info('Nessun risultato per i filtri selezionati.')
elif section != '🏷️ Categorie':
    pages = (count + page_size - 1) // page_size
    current = st.number_input('Pagina', min_value=1, max_value=pages, value=1, step=1)
    order = {'Venduti più recenti':'ended_at DESC, first_seen DESC', 'Prezzo crescente':'sold_price ASC, ended_at DESC', 'Prezzo decrescente':'sold_price DESC, ended_at DESC'}[sort]
    with connect() as con:
        columns = {r[1] for r in con.execute('PRAGMA table_info(sales)')}
    start_col = 'posted_at' if 'posted_at' in columns else ('listed_at' if 'listed_at' in columns else None)
    select_start = ', ' + start_col + ' AS listed_at' if start_col else ', NULL AS listed_at'
    data = fetch('SELECT image, ended_at, title, sold_price, currency, url' + select_start + ' FROM sales WHERE ' + where_sql + ' ORDER BY ' + order + ' LIMIT ? OFFSET ?', tuple(params + [int(page_size), (int(current)-1)*page_size]))

    def safe_link(raw):
        value = str(raw or '').strip()
        parsed = urlparse(value)
        if parsed.scheme != 'https' or not (parsed.hostname and (parsed.hostname == 'ebay.it' or parsed.hostname.endswith('.ebay.it') or parsed.hostname == 'ebay.com' or parsed.hostname.endswith('.ebay.com'))):
            return ''
        return escape(value, quote=True)

    def sold_speed(row):
        # A date of sale alone cannot determine how long a listing took to sell.
        if pd.isna(row.get('listed_at')) or pd.isna(row.get('ended_at')):
            return '<span class="muted" title="Data di pubblicazione non disponibile">—</span>'
        start = pd.to_datetime(row['listed_at'], utc=True, errors='coerce')
        end = pd.to_datetime(row['ended_at'], utc=True, errors='coerce')
        if pd.isna(start) or pd.isna(end) or end < start:
            return '—'
        hours = (end - start).total_seconds() / 3600
        label = f'{hours:.1f} ore' if hours < 24 else f'{hours / 24:.1f} giorni'
        fires = '🔥🔥🔥🔥' if hours <= 6 else '🔥🔥🔥' if hours <= 12 else '🔥🔥' if hours <= 24 else '🔥' if hours <= 48 else '🐢'
        return f'{fires} {label}'

    rows = []
    for _, item in data.iterrows():
        link = safe_link(item['url'])
        title = escape(str(item['title'] if pd.notna(item['title']) else 'Senza titolo'))
        title_cell = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>' if link else title
        image_url = str(item['image']) if pd.notna(item['image']) else ''
        image_ok = urlparse(image_url).scheme == 'https'
        image_cell = f'<img src="{escape(image_url, quote=True)}" alt="Foto annuncio" loading="lazy">' if image_ok else '—'
        date_str = escape(str(item['ended_at'] or '—'))[:10]
        price_str = eur(item['sold_price'])
        rows.append(f'<tr><td>{image_cell}</td><td>{title_cell}</td><td class="price">{price_str}</td><td>{date_str}</td><td>{sold_speed(item)}</td></tr>')
    html_table = ('<div class="mt-scroll"><table class="mt-sale-table"><thead><tr>'
                  '<th>Foto</th><th>Annuncio (clicca per aprire)</th><th>Prezzo</th><th>Venduto il</th><th>🔥 Venduto in</th>'
                  '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')
    st.markdown(html_table, unsafe_allow_html=True)
    st.caption('🔥 Venduto in: calcolato solo quando è disponibile anche la data di pubblicazione. Al momento SoldComps ci restituisce la data di vendita, non la durata dell’inserzione.')
    st.caption(f'Pagina {current} di {pages} · {count:,} risultati · caricati solo {len(data)} annunci'.replace(',','.'))
    st.download_button('⬇️ Esporta questa pagina (CSV)', data=data.to_csv(index=False).encode('utf-8-sig'), file_name='venduti_ebay_pagina.csv', mime='text/csv')

with st.expander('📈 Andamento dei venduti archiviati', expanded=(section == '📊 Dashboard')):
    trends = fetch('SELECT substr(ended_at,1,10) giorno, COUNT(*) venduti FROM sales WHERE ' + where_sql + ' AND ended_at IS NOT NULL GROUP BY substr(ended_at,1,10) ORDER BY giorno', tuple(params))
    if not trends.empty:
        st.line_chart(trends, x='giorno', y='venduti', width='stretch')
    else:
        st.info('Nessuna data disponibile.')

with st.expander('🛰️ Ultimi controlli API', expanded=False):
    try:
        runs = fetch('SELECT ran_at, items_seen, inserted, status, message FROM runs ORDER BY id DESC LIMIT 12')
        st.dataframe(runs, hide_index=True, width='stretch')
    except sqlite3.OperationalError:
        st.info('Storico controlli non disponibile.')
st.caption('Dati SoldComps: i prezzi visibili potrebbero non rappresentare il prezzo effettivo delle offerte accettate. La dashboard non genera richieste API.')
