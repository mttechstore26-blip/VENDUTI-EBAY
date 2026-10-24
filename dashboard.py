"""Venduti eBay: fast SQLite-backed Streamlit dashboard, category-wide collection unchanged."""
import os
import math
from datetime import date, datetime
from zoneinfo import ZoneInfo
import requests
import sqlite3
from html import escape
from urllib.parse import urlparse
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from ebay_taxonomy import classify
from kitchen_taxonomy import classify_kitchen
from coffee_taxonomy import classify_coffee
from console_taxonomy import classify_console
from apple_laptop_taxonomy import classify_apple_laptop
from laptop_taxonomy import classify_laptop
from monitor_taxonomy import classify_monitor
from camera_taxonomy import classify_camera
from tablet_taxonomy import classify_tablet
from location_flags import flag_for_location
from eu_locations import is_eu_location

load_dotenv(Path(__file__).resolve().parent / '.env')

def max_buy_price(sale_price):
    """Highest viable purchase price with the user's minimum margins."""
    try:
        p = float(sale_price)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(p) or p <= 0:
        return None
    candidates = []
    for minimum, maximum, desired in ((10, 50, 25), (51, 100, 30), (101, float('inf'), 40)):
        ceiling = min(maximum, p - desired)
        if ceiling >= minimum:
            candidates.append((ceiling, desired))
    return max(candidates)[0] if candidates else None

def watchlist_db():
    with sqlite3.connect(DB, timeout=20) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS model_watchlist (
            category_id TEXT NOT NULL, model_name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(category_id,model_name))""")

def watchlist_names(category_id):
    watchlist_db()
    with sqlite3.connect(DB, timeout=20) as conn:
        return {row[0] for row in conn.execute(
            "SELECT model_name FROM model_watchlist WHERE category_id=?",
            (str(category_id),)).fetchall()}

def watchlist_change(category_id, model_name, add):
    watchlist_db()
    with sqlite3.connect(DB, timeout=20) as conn:
        if add:
            conn.execute("INSERT OR IGNORE INTO model_watchlist(category_id,model_name) VALUES(?,?)",
                         (str(category_id),str(model_name)))
        else:
            conn.execute("DELETE FROM model_watchlist WHERE category_id=? AND model_name=?",
                         (str(category_id),str(model_name)))


ACTIVE_CATEGORIES = ('141755', '63', '717', '233', '183446', '101376', '20667', '38250', '139971','111422','175672','80053','31388','171485')
st.set_page_config(page_title='Venduti eBay | MT TECH', page_icon='📚', layout='wide')
# Compact styling without replacing Streamlit's selection-enabled dataframe.
st.markdown("""
<style>
section[data-testid="stSidebar"] {background:#f8fafc;border-right:1px solid #e2e8f0}
div[data-testid="stDataFrame"] {border:1px solid #dce5f0;border-radius:13px;overflow:hidden}
div[data-testid="stExpander"] {border-radius:11px}
</style>
""", unsafe_allow_html=True)

DB = (Path(__file__).resolve().parent / os.getenv('DB_PATH', './data/ebay_sold.db')).resolve()

st.markdown('''<style>
.stApp {background:radial-gradient(circle at 8% 0%,#e8efff 0%,transparent 31%),linear-gradient(180deg,#fbfdff,#f0f4fa)}
.block-container {max-width:1650px;padding-top:1.3rem} html,body,[data-testid='stAppViewContainer'] {font-size:17px!important} .stMarkdown p,.stCaption,.stSelectbox label,.stTextInput label,.stNumberInput label,.stRadio label {font-size:16px!important} section[data-testid='stSidebar'] {min-width:285px} div[data-testid='stMetricLabel']{font-size:17px} div[data-testid='stMetricValue']{font-size:31px} div[data-testid='stDataFrame']{font-size:16px} button, input,select{font-size:16px!important}
h1,h2,h3 {letter-spacing:-.035em;color:#0f172a}
div[data-testid="stMetric"] {background:#ffffffde;border:1px solid #e2e8f0;border-radius:19px;padding:18px 20px;box-shadow:0 9px 27px #0f172a0a}
div[data-testid="stMetric"]:before {content:"";display:block;height:3px;background:linear-gradient(90deg,#2563eb,#7c3aed);margin:-18px -20px 13px;border-radius:19px 19px 0 0}
div[data-testid="stDataFrame"] {border-radius:15px;overflow:hidden}
.mt-hero {padding:25px 29px;color:white;border-radius:24px;background:radial-gradient(circle at 93% 10%,#564cba 0%,transparent 34%),linear-gradient(125deg,#101a33,#1e3566 65%,#312e81);box-shadow:0 15px 35px #0f172a20;margin-bottom:16px}
.mt-title {font-size:37px;font-weight:850;letter-spacing:-1px}.mt-subtitle{color:#cad4e8;font-size:17px;margin-top:6px}

.mt-sale-table{width:100%;border-collapse:separate;border-spacing:0;background:white;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;font-size:16px}
.mt-sale-table th{background:#f1f5f9;color:#475569;font-size:15px;text-align:left;padding:13px 10px;position:sticky;top:0}
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


# Read-only subscription usage endpoint, cached across Streamlit sessions for an hour.
# Never put the API key in HTML, logs, or GitHub.
@st.cache_data(ttl=3600, show_spinner=False)
def soldcomps_credits_remaining():
    api_key = os.getenv('SOLDCOMPS_API_KEY', '').strip()
    if not api_key:
        return None
    try:
        response = requests.get(
            'https://api.sold-comps.com/usage',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=(4, 10),
        )
        response.raise_for_status()
        return int(response.json()['usage']['remaining'])
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None

credits_left = soldcomps_credits_remaining()
target_day = date(2026, 11, 18)
days_to_target = max(0, (target_day - datetime.now(ZoneInfo('Europe/Rome')).date()).days)
daily_planned = len(ACTIVE_CATEGORIES) * 4
planned_needed = days_to_target * daily_planned
if credits_left is None:
    st.caption('💳 SoldComps: saldo momentaneamente non disponibile; nessuna raccolta avviata dalla dashboard.')
else:
    reserve = credits_left - planned_needed
    status_text = (
        f'✅ In linea · margine stimato {reserve:,} crediti'
        if reserve >= 0 else f'⚠️ Rischio esaurimento · mancano {-reserve:,} crediti'
    )
    banner_color = '#166534' if reserve >= 0 else '#9a3412'
    banner_bg = '#f0fdf4' if reserve >= 0 else '#fff7ed'
    st.markdown(
        f'<div style="background:{banner_bg};border:1px solid {banner_color}55;'
        f'border-radius:14px;padding:14px 18px;margin:4px 0 18px">'
        f'<div style="font-size:15px;font-weight:700;color:{banner_color}">💳 Crediti SoldComps disponibili</div>'
        f'<div style="font-size:28px;font-weight:850;color:#0f172a">{credits_left:,}</div>'
        f'<div style="color:#334155;font-size:14px">Consumo programmato: fino a {daily_planned} al giorno'
        f' · Fabbisogno stimato fino al 18/11: {planned_needed:,}'
        f' · {days_to_target} giorni rimanenti</div>'
        f'<div style="font-weight:700;color:{banner_color};margin-top:5px">{status_text}</div>'
        f'<div style="font-size:12px;color:#64748b">Saldo API aggiornato al massimo ogni ora.'
        f' Previsione senza recuperi storici o test extra.</div></div>',
        unsafe_allow_html=True,
    )


if not DB.is_file():
    st.warning('Database non trovato. Verifica DB_PATH nel file .env.')
    st.stop()

# Manual taxonomy corrections live in SQLite, not in git-tracked code.
APPLE_MODEL_CORRECTIONS = {
    '227558428111': 'MacBook Pro Intel 15" (2015)',
    '880018340440': 'MacBook Pro Intel 15" (2017)',
    '267784952522': 'MacBook Pro Intel 15" (2014)',
    '137728242591': 'MacBook Pro Intel 15" (2017)',
}

def manual_taxonomy_rows():
    with connect() as conn:
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='taxonomy_overrides'").fetchone()
        if not exists:
            return {}
        return {(str(a), str(b)): (brand, family, model) for a,b,brand,family,model in
                conn.execute("SELECT category_id,item_id,brand,family,model FROM taxonomy_overrides")}

def save_taxonomy_override(category_id, item_id, brand, family, model):
    with sqlite3.connect(DB, timeout=15) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS taxonomy_overrides (
            category_id TEXT NOT NULL, item_id TEXT NOT NULL,
            brand TEXT NOT NULL, family TEXT NOT NULL, model TEXT NOT NULL,
            PRIMARY KEY(category_id,item_id))""")
        conn.execute("""INSERT INTO taxonomy_overrides(category_id,item_id,brand,family,model)
                        VALUES (?,?,?,?,?)
                        ON CONFLICT(category_id,item_id) DO UPDATE SET
                        brand=excluded.brand,family=excluded.family,model=excluded.model""",
                     (category_id,item_id,brand,family,model))
        conn.commit()

def connect():
    uri = f'file:{DB.as_posix()}?mode=ro'
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.execute('PRAGMA busy_timeout=5000')
    conn.create_function('is_eu_location', 1, lambda loc: int(is_eu_location(loc)))
    return conn

@st.cache_data(ttl=40, show_spinner=False)
def fetch(sql, params=()):
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)

@st.cache_data(ttl=40, show_spinner=False)
def load_categories():
    return fetch('''SELECT c.category_id, c.name, COUNT(s.item_id) AS n
                    FROM categories c LEFT JOIN sales s ON s.category_id=c.category_id AND s.sold_price>=70
                      AND (s.category_id NOT IN ('139971','171485') OR (((s.category_id='139971' AND s.sold_price>=300) OR (s.category_id='171485' AND s.sold_price BETWEEN 100 AND 250)) AND is_eu_location(s.item_location)=1))
                    WHERE c.category_id IN ('141755','63','717','233','183446','101376','20667','38250','139971','111422','175672','80053','31388','171485')
                    GROUP BY c.category_id,c.name ORDER BY n DESC, c.name ASC''')

if 'category_id' not in [r[1] for r in sqlite3.connect(DB).execute('PRAGMA table_info(sales)').fetchall()]:
    st.error('Database da aggiornare: esegui prima upgrade_categories.py sulla VPS.')
    st.stop()

try:
    category_df=load_categories()
except sqlite3.OperationalError:
    st.error('Tabella categorie mancante: esegui upgrade_categories.py sulla VPS.')
    st.stop()

CATEGORY_ICONS = {
    '141755':'⚽', '63':'📚', '717':'🧸', '233':'🎲',
    '183446':'🧱', '101376':'🪆', '20667':'🍳', '38250':'☕',
    '139971':'🎮', '111422':'🍎', '175672':'💻', '80053':'🖥️', '31388':'📷', '171485':'📱',
}
category_df = category_df.sort_values(['n','name'], ascending=[False,True], kind='stable')
names={str(r.category_id): f"{CATEGORY_ICONS.get(str(r.category_id),'📦')} {r.name} ({int(r.n)} venduti)" for r in category_df.itertuples(index=False)}


with st.sidebar:
    st.header('📂 Navigazione')
    section = st.radio('Sezione', ['📦 Annunci venduti', '🏷️ Categorie'])
    category_opt = st.selectbox('Categoria', ['Tutte le categorie'] + list(names), format_func=lambda k: names.get(k, k))
    selected_category = None if category_opt == 'Tutte le categorie' else category_opt
    if selected_category is not None:
        # Runs are not tagged by category: show a recent insertion window, not a per-category run.
        # The scheduler runs all categories in a six-hour cycle. Use insertion
        # timestamps, not ended_at (the original sale date), for NEW items.
        # This also works with historical runs which have no category_id field.
        latest_cycle = fetch("""
            SELECT MAX(ran_at) AS last_run
            FROM runs WHERE status = 'ok'
        """)
        if not latest_cycle.empty and pd.notna(latest_cycle.iloc[0]['last_run']):
            last_run = pd.to_datetime(latest_cycle.iloc[0]['last_run'], utc=True)
            cycle_start = last_run.floor('6h')
            cycle_end = last_run + pd.Timedelta(seconds=1)
            new_sales = fetch("""
                SELECT COUNT(*) AS new_count FROM sales
                WHERE category_id = ?
                  AND (category_id NOT IN ('139971','171485') OR (((category_id='139971' AND sold_price>=300) OR (category_id='171485' AND sold_price BETWEEN 100 AND 250)) AND is_eu_location(item_location)=1))
                  AND first_seen >= ? AND first_seen < ?
            """, (selected_category, cycle_start.isoformat(), cycle_end.isoformat()))
            count = int(new_sales.iloc[0]['new_count'])
            local_time = last_run.tz_convert('Europe/Rome')
            st.markdown(
                f'<div style="background:#ffffff;border:1px solid #dbe4ef;'
                f'border-radius:12px;padding:10px 12px;margin:2px 0 6px 0;">'
                f'<div style="font-size:13px;color:#64748b;">🔄 Ultimo controllo API globale · '
                f'{local_time.strftime("%d/%m/%Y %H:%M")}</div>'
                f'<div style="font-size:17px;font-weight:700;color:#15803d;">'
                f'+{count} nuovi venduti nel ciclo recente (stima)</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption('🔄 Nessuna raccolta disponibile.')
    st.divider()
    st.header('🔎 Filtri')
    search = st.text_input('🔎 Cerca prodotto venduto', placeholder='Es. Mexico 86, Dylan Dog 1, Argentina 78…', help='Cerca tra gli annunci già presenti nel database, senza consumare crediti SoldComps.')
    period = st.selectbox('Periodo', ['Tutti', 'Ultimi 7 giorni', 'Ultimi 30 giorni', 'Ultimi 90 giorni', 'Ultimi 365 giorni'])
    condition = st.selectbox('Condizione', ['Tutte', 'Nuovo', 'Di seconda mano'])
    max_df = fetch("SELECT MAX(sold_price) hi FROM sales WHERE sold_price>=70 AND (category_id NOT IN ('139971','171485') OR (((category_id='139971' AND sold_price>=300) OR (category_id='171485' AND sold_price BETWEEN 100 AND 250)) AND is_eu_location(item_location)=1)) AND category_id IN ('141755','63','717','233','183446','101376','20667','38250','139971','111422','175672','80053','31388','171485')")
    highest = int(max(70, max_df.iloc[0]['hi'] or 70))
    price_low = st.number_input('Prezzo minimo visualizzato (€)', min_value=70, max_value=max(70,highest), value=70, step=10)
    price_high = st.number_input('Prezzo massimo visualizzato (€)', min_value=int(price_low), value=max(highest,int(price_low)), step=20)
    sort = st.selectbox('Ordina', ['Venduti più recenti', 'Prezzo crescente', 'Prezzo decrescente'])
    page_size = st.selectbox('Annunci per pagina', [25, 50, 100], index=1)
    if st.button('↻ Aggiorna dati', width='stretch'):
        fetch.clear()
        load_categories.clear()
        st.rerun()

where = ["category_id IN ('141755','63','717','233','183446','101376','20667','38250','139971','111422','175672','80053','31388','171485')", 'sold_price >= ?', 'sold_price >= ?', 'sold_price <= ?']
params = [70, float(price_low), float(price_high)]
if selected_category is not None:
    where.append('category_id = ?')
    params.append(selected_category)
if search.strip():
    # All words must occur, in any order. Accept common title variants.
    import re
    words = [w for w in re.split(r"[,;\s]+", search.casefold().strip()) if w]
    for word in words:
        variants = [word]
        if word in ("mexico", "messico", "méxico"):
            variants = ["mexico", "messico", "méxico"]
        elif word in ("86", "78", "82", "90", "94", "98"):
            variants = [word, "19" + word]
        clauses = []
        for variant in variants:
            clauses.append('LOWER(COALESCE(title, "")) LIKE ?')
            params.append('%' + variant + '%')
        where.append('(' + ' OR '.join(clauses) + ')')
if period != 'Tutti':
    days = {'Ultimi 7 giorni':7,'Ultimi 30 giorni':30,'Ultimi 90 giorni':90,'Ultimi 365 giorni':365}[period]
    where.append("date(ended_at) >= date('now', ?)")
    params.append(f'-{days} days')
if condition != 'Tutte':
    where.append('condition = ?')
    params.append(condition)
where.append("(category_id NOT IN ('139971','171485') OR (((category_id='139971' AND sold_price>=300) OR (category_id='171485' AND sold_price BETWEEN 100 AND 250)) AND is_eu_location(item_location)=1))")
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

if search.strip() and section != '🏷️ Categorie':
    st.info(f'🔎 Ricerca: **{search}** · **{count}** venduti trovati nell’archivio eBay. I risultati dipendono dalle vendite già raccolte.')

if section == '🏷️ Categorie':
    st.subheader('🎯 Esplora una categoria')
    st.caption('Radar famiglie dei venduti eBay · stesso flusso di Venduti Subito')
    @st.cache_data(ttl=60, show_spinner=False)
    def taxonomy_data(category_filter=None):
        raw = fetch("""SELECT s.item_id, s.category_id, COALESCE(c.name,s.category_id) AS category_name,
                         s.title, s.sold_price, s.ended_at, s.url, s.image, s.item_location, s.seller
                         FROM sales s LEFT JOIN categories c ON c.category_id=s.category_id
                         WHERE s.sold_price>=70 AND (s.category_id NOT IN ('139971','171485') OR (((s.category_id='139971' AND s.sold_price>=300) OR (s.category_id='171485' AND s.sold_price BETWEEN 100 AND 250)) AND is_eu_location(s.item_location)=1)) AND s.category_id IN ('141755','63','717','233','183446','101376','20667','38250','139971','111422','175672','80053','31388','171485')""")
        if category_filter is not None:
            raw = raw[raw['category_id'].astype(str) == str(category_filter)].copy()
        if raw.empty:
            return raw
        parsed = []
        for r in raw.itertuples(index=False):
            if str(r.category_id) == '20667':
                parsed.append(classify_kitchen(r.title))
            elif str(r.category_id) == '38250':
                parsed.append(classify_coffee(r.title))
            elif str(r.category_id) == '139971':
                parsed.append(classify_console(r.title))
            elif str(r.category_id) == '111422':
                parsed.append(classify_apple_laptop(r.title))
            elif str(r.category_id) == '175672':
                parsed.append(classify_laptop(r.title))
            elif str(r.category_id) == '80053':
                parsed.append(classify_monitor(r.title))
            elif str(r.category_id) == '31388':
                parsed.append(classify_camera(r.title))
            elif str(r.category_id) == '171485':
                parsed.append(classify_tablet(r.title))
            else:
                parsed.append((*classify(r.category_id, r.title), 'Non applicabile'))
        raw[['Brand / Editore','Famiglia / Serie','Modello / Edizione','Stato prodotto']] = pd.DataFrame(parsed,index=raw.index)
        for item_id, model_name in APPLE_MODEL_CORRECTIONS.items():
            mask = raw['category_id'].astype(str).isin(['111422', '175672']) & raw['item_id'].astype(str).eq(item_id)
            raw.loc[mask, ['Brand / Editore','Famiglia / Serie','Modello / Edizione']] = ['Apple', 'MacBook Pro', model_name]
        # Explicit per-listing Air correction, including a group not previously present.
        air_2020 = raw['category_id'].astype(str).isin(['111422', '175672']) & raw['item_id'].astype(str).eq('307175793216')
        raw.loc[air_2020, ['Brand / Editore','Famiglia / Serie','Modello / Edizione']] = ['Apple', 'MacBook Air', 'MacBook Air 13" (2020)']
        # Database overrides always take precedence over hardcoded corrections.
        overrides = manual_taxonomy_rows()
        for idx, row in raw.iterrows():
            override = overrides.get((str(row['category_id']), str(row['item_id'])))
            if override:
                raw.loc[idx, ['Brand / Editore','Famiglia / Serie','Modello / Edizione']] = list(override)
        # Promote repeated identifiable models to their own clickable family.
        # Keep the source family as a grouping key: comic issue 1 in one series
        # must never be mixed with issue 1 in another series.
        valid = (~raw['Modello / Edizione'].str.contains(
                    'non identificat|da identificare|non specificat|variante da verificare',
                    case=False, na=True, regex=True)
                 & raw['Modello / Edizione'].notna())
        counts = raw.loc[valid].groupby(
            ['category_id','Famiglia / Serie','Modello / Edizione'],dropna=False
        )['item_id'].transform('size')
        repeated = counts[counts >= 2].index
        if len(repeated):
            source_family = raw.loc[repeated,'Famiglia / Serie'].astype(str)
            model = raw.loc[repeated,'Modello / Edizione'].astype(str)
            lego = (raw.loc[repeated,'Brand / Editore'].eq('LEGO')
                    & model.str.fullmatch(r'\\d{4,6}'))
            promoted = source_family + ' — ' + model
            promoted.loc[lego] = 'LEGO ' + model.loc[lego]
            raw.loc[repeated,'Famiglia / Serie'] = promoted
        return raw

    taxonomy = taxonomy_data(selected_category)
    if taxonomy.empty:
        st.info('Nessun venduto disponibile per questa categoria.')
    else:
        categories = sorted(taxonomy['category_name'].dropna().unique().tolist())
        cat_name = categories[0] if len(categories) == 1 else st.selectbox('Categoria da analizzare',categories,key='radar_category')
        subset = taxonomy[taxonomy['category_name']==cat_name]
        if str(subset['category_id'].iloc[0]) == '111422':
            apple_period = st.selectbox('Periodo vendite Apple', ['Tutti i periodi', '1–19 ottobre 2026'], key='apple_history_period')
            if apple_period == '1–19 ottobre 2026':
                subset = subset[(subset['ended_at'].astype(str).str[:10] >= '2026-10-01') & (subset['ended_at'].astype(str).str[:10] <= '2026-10-19')].copy()
                st.caption(f'📅 {len(subset)} venduti dal 1 al 19 ottobre 2026. Il filtro si applica a modelli, prezzi e CSV.')
        # Classifiche coerenti con i filtri generali della sidebar.
        if search.strip():
            for word in words:
                variants = ['mexico', 'messico', 'méxico'] if word in ('mexico','messico','méxico') else ([word, '19'+word] if word in ('86','78','82','90','94','98') else [word])
                subset = subset[subset['title'].fillna('').str.casefold().apply(lambda t: any(v in t for v in variants))]
        subset = subset[(subset['sold_price'] >= float(price_low)) & (subset['sold_price'] <= float(price_high))]
        if period != 'Tutti':
            days = {'Ultimi 7 giorni':7,'Ultimi 30 giorni':30,'Ultimi 90 giorni':90,'Ultimi 365 giorni':365}[period]
            dates = pd.to_datetime(subset['ended_at'], errors='coerce', utc=True)
            subset = subset[dates >= pd.Timestamp.now(tz='UTC').normalize() - pd.Timedelta(days=days)]
        if condition != 'Tutte':
            st.caption('Nota: il filtro Condizione è disponibile nella sezione Annunci; non applicato alle classifiche.')
        if subset.empty:
            st.info('Nessun prodotto corrisponde ai filtri della categoria.')
            st.stop()
        with st.expander('✏️ Organizza prodotti · spostamento rapido', expanded=False):
            st.caption('Trova un annuncio, seleziona una famiglia esistente e salva. Le modifiche sono permanenti e aggiornano le classifiche.')
            editor_password = os.getenv('EBAY_EDITOR_PASSWORD', '').strip()
            if not editor_password:
                st.warning('Editor non configurato: imposta EBAY_EDITOR_PASSWORD nel file .env della VPS.')
            else:
                from hmac import compare_digest
                password = st.text_input('🔒 Password editor', type='password', key='taxonomy_editor_password')
                if compare_digest(password, editor_password) and bool(password):
                    lookup = st.text_input('🔍 Cerca per ID o titolo', placeholder='Es. 227558428111 oppure MacBook Pro', key='taxonomy_lookup')
                    candidates = subset.copy()
                    if lookup.strip():
                        term = lookup.strip().casefold()
                        candidates = candidates[
                            candidates['item_id'].astype(str).str.contains(term, case=False, regex=False)
                            | candidates['title'].fillna('').astype(str).str.contains(term, case=False, regex=False)
                        ]
                    candidates = candidates.sort_values('ended_at', ascending=False).head(150)
                    if candidates.empty:
                        st.info('Nessun annuncio trovato. Modifica la ricerca.')
                    else:
                        item_options = list(candidates['item_id'].astype(str))
                        item_labels = {str(r.item_id): f"{r.item_id} · {str(r.title)[:90]} · {eur(r.sold_price)}"
                                       for r in candidates.itertuples(index=False)}
                        chosen_item = st.selectbox('1 · Scegli il prodotto', item_options,
                                                   format_func=lambda v: item_labels.get(v,v))
                        current = candidates[candidates['item_id'].astype(str).eq(chosen_item)].iloc[0]
                        current_brand = str(current['Brand / Editore'])
                        current_family = str(current['Famiglia / Serie'])
                        current_model = str(current['Modello / Edizione'])
                        st.caption(f"Attuale: {current_brand} → {current_family} → {current_model}")
                        model_grouped = str(current['category_id']) in ('111422','175672','20667','38250','139971')
                        if model_grouped:
                            # These dashboards rank by model: one destination is enough.
                            existing = sorted(set(subset['Modello / Edizione'].dropna().astype(str)) | {current_model})
                            destination = st.selectbox('2 · Sposta nel modello / gruppo',
                                ['➕ Crea nuovo gruppo'] + existing,
                                index=existing.index(current_model)+1,
                                key=f'taxonomy_destination_{chosen_item}')
                            model_final = (st.text_input('Nome del nuovo gruppo', max_chars=180,
                                            key=f'taxonomy_new_destination_{chosen_item}').strip()
                                           if destination == '➕ Crea nuovo gruppo' else destination)
                            # Derive brand and family from an existing member of the target group.
                            target = subset[subset['Modello / Edizione'].astype(str).eq(model_final)]
                            if not target.empty:
                                brand_final = str(target.iloc[0]['Brand / Editore'])
                                family_final = str(target.iloc[0]['Famiglia / Serie'])
                            else:
                                brand_final, family_final = current_brand, current_family
                            st.caption(f'📍 Destinazione: {model_final or "Inserisci il nome del gruppo"}')
                        else:
                            brands = sorted(set(subset['Brand / Editore'].dropna().astype(str)) | {current_brand})
                            brand_choice = st.selectbox('2 · Brand', ['➕ Nuovo brand'] + brands,
                                                        index=brands.index(current_brand)+1)
                            brand_final = (st.text_input('Nome nuovo brand').strip()
                                           if brand_choice == '➕ Nuovo brand' else brand_choice)
                            known_families = sorted(set(subset.loc[
                                subset['Brand / Editore'].astype(str).eq(brand_final),
                                'Famiglia / Serie'].dropna().astype(str)) | {current_family})
                            family_choice = st.selectbox('3 · Famiglia',
                                ['➕ Nuova famiglia'] + known_families,
                                index=known_families.index(current_family)+1)
                            family_final = (st.text_input('Nome nuova famiglia').strip()
                                            if family_choice == '➕ Nuova famiglia' else family_choice)
                            model_final = st.text_input('4 · Modello / edizione',
                                value=current_model, key=f'taxonomy_model_{chosen_item}')
                        submitted = st.button('💾 Sposta prodotto e aggiorna classifiche', type='primary', key='taxonomy_save')
                        if submitted:
                            if not all(str(v).strip() for v in (brand_final, family_final, model_final)):
                                st.error('Compila brand, famiglia e modello.')
                            else:
                                save_taxonomy_override(str(current['category_id']), chosen_item,
                                                       brand_final.strip(), family_final.strip(), model_final.strip())
                                taxonomy_data.clear()
                                fetch.clear()
                                st.success('Prodotto spostato: la scelta è stata salvata.')
                                st.rerun()
                elif password:
                    st.error('Password non corretta.')
        # Export completo, indipendente dalla selezione delle famiglie.
        # Usa i dati SQLite gia raccolti: nessuna richiesta SoldComps.
        export_rows = subset.sort_values('ended_at', ascending=False).copy()
        export_rows = export_rows.rename(columns={
            'category_name': 'Categoria', 'category_id': 'ID categoria',
            'item_id': 'ID annuncio', 'title': 'Titolo',
            'sold_price': 'Prezzo venduto EUR', 'ended_at': 'Data vendita',
            'url': 'URL annuncio', 'image': 'URL immagine',
        })
        export_id = str(subset['category_id'].iloc[0])
        st.download_button(
            f"📥 Scarica CSV completo della categoria ({len(export_rows)} venduti)",
            data=export_rows.to_csv(index=False).encode('utf-8-sig'),
            file_name=f"venduti_ebay_categoria_{export_id}.csv",
            mime='text/csv',
            key=f"download_category_{export_id}",
            help="Esporta tutti i venduti archiviati della categoria con brand, famiglia, modello, prezzi e date. Non consuma richieste SoldComps."
        )
        if export_id == '175672':
            # Exclusive, auditable groups: lots and defective units must not distort
            # single working-laptop median prices or demand rankings.
            subset = subset.copy()
            status_text = subset['Stato prodotto'].fillna('').astype(str)
            model_text = subset['Modello / Edizione'].fillna('').astype(str)
            unknown = model_text.str.contains(
                r'da identificare|non identificat|non specificat|da verificare|variante non specificata|anno non specificato',
                case=False, regex=True)
            multiple = status_text.str.contains('Lotto multiplo',case=False,regex=False)
            defective = status_text.str.contains('guast|ricamb|blocc|difett|da verificare|condizioni',
                                                case=False,regex=True)
            subset['Segmento portatile'] = 'Singolo completo (presunto)'
            subset.loc[unknown, 'Segmento portatile'] = 'Modello non identificato'
            subset.loc[defective, 'Segmento portatile'] = 'Guasto / ricambi / da verificare'
            subset.loc[multiple, 'Segmento portatile'] = 'Lotto multiplo'
            segment_order = ['Singolo completo (presunto)', 'Guasto / ricambi / da verificare',
                             'Lotto multiplo', 'Modello non identificato']
            segment_counts = subset['Segmento portatile'].value_counts()
            st.caption('📊 Segmentazione dei portatili archiviati (titoli indicativi, non verifiche fisiche): ' +
                       ' · '.join(f'{name}: {int(segment_counts.get(name,0))}' for name in segment_order))
            segment_choice = st.selectbox(
                'Classifica portatili', ['Singolo completo (presunto)', 'Tutti'] +
                [name for name in segment_order if name != 'Singolo completo (presunto)'],
                help='La classifica predefinita esclude lotti, guasti e modelli non identificati; '
                     'seleziona Tutti per includere ogni annuncio.')
            if segment_choice != 'Tutti':
                subset = subset[subset['Segmento portatile'] == segment_choice].copy()
            if subset.empty:
                st.info('Nessun portatile in questo segmento con i filtri selezionati.')
                st.stop()
        if export_id in ('20667','38250','139971','111422','175672'):
            state_choice = st.selectbox(
                'Tipo prodotto', ['Tutti'] + sorted(subset['Stato prodotto'].dropna().unique().tolist()),
                help='Classificazione indicativa ricavata dal titolo; non sostituisce una verifica dell’annuncio.')
            if state_choice != 'Tutti':
                subset = subset[subset['Stato prodotto'] == state_choice]

        if export_id == '183446':
            import re
            subset = subset.copy()
            def lego_type(row):
                title = str(row['title'] or '').casefold()
                brand = str(row['Brand / Editore'] or '')
                if brand != 'LEGO':
                    return 'Altre costruzioni'
                if re.search(r'\b(?:solo\s+(?:scatola|box|istruzioni|manuale)|empty\s+box|box\s+only|instructions?\s+only|manual\s+only|ricambi|spare\s+parts|replacement\s+parts)\b', title):
                    return 'Accessori / scatole / ricambi'
                if re.search(r'\b(?:minifig(?:ure)?s?|personaggi\s+lego|cmf|lego\s+figure)\b', title):
                    return 'Minifigure / personaggi'
                if re.search(r'\b(?:lotto|lotti|lot\s+of|bulk\s+lego|sfuso|mixed\s+bricks|misti)\b', title):
                    return 'Lotti / pezzi misti'
                if re.search(r'\b(?:replica|riproduzione|imitazione|counterfeit|fake|bootleg|moc|custom\s+build|compatibile|compatible\s+with\s+lego|non\s+lego)\b', title):
                    return 'MOC / compatibili'
                if re.search(r'\b(?:incomplet[oaie]|pezzi\s+mancanti|missing\s+pieces|non\s+completo|without\s+pieces)\b', title):
                    return 'Set incompleti / pezzi mancanti'
                return 'Set LEGO (completezza da verificare)'
            subset['Tipo costruzione'] = subset.apply(lego_type, axis=1)
            kinds = ['Set LEGO (completezza da verificare)', 'Set incompleti / pezzi mancanti',
                     'Minifigure / personaggi', 'Lotti / pezzi misti',
                     'Accessori / scatole / ricambi', 'MOC / compatibili', 'Altre costruzioni']
            counts_by_type = subset['Tipo costruzione'].value_counts()
            st.caption('📦 ' + ' · '.join(f'{x}: {int(counts_by_type.get(x,0))}' for x in kinds))
            kind_choice = st.selectbox('Tipologia LEGO', ['Tutti'] + kinds,
                help='Il codice set viene riconosciuto indipendentemente dallo stato e dalla tipologia.')
            def lego_model(row):
                if str(row['Brand / Editore']) != 'LEGO':
                    return str(row['Famiglia / Serie'])
                title = str(row['title'] or '').casefold()
                kind = str(row['Tipo costruzione'])
                if kind == 'Minifigure / personaggi':
                    ids = list(dict.fromkeys(re.findall(r'(?<![a-z0-9])((?:sw|bat|col|hp|njo|sh|dis|lor|cas|cty|sp|pi)\d{3,5})(?![a-z0-9])', title)))
                    if len(ids) == 1:
                        return 'Minifigure ' + ids[0].upper()
                    return 'Minifigure — ID non identificato' if not ids else 'Minifigure — più ID'
                if kind in ('Lotti / pezzi misti','Accessori / scatole / ricambi','MOC / compatibili'):
                    return 'LEGO — ' + kind
                # Common vintage 3-digit sets and explicit 7-digit promotional sets.
                # Three-digit extraction is strictly whitelisted to avoid years, quantities and prices.
                vintage = {'928','924','886','371','306'}
                promo = {'5000063','5004077','4002019'}
                tokens = list(re.finditer(r'(?<![a-z0-9])(\d{3,7})(?:-2)?(?![a-z0-9])', title))
                def valid_match(match):
                    value=match.group(1)
                    number=int(value)
                    suffix=title[match.end():match.end()+18]
                    if re.match(r'\s*(?:pz\b|pzs\b|pezzi\b|pieces\b|pcs\b|parts\b|teil(?:e)?\b|briques\b)',suffix):
                        return False
                    if len(value)==3:
                        return value in vintage
                    if len(value)==7:
                        return value in promo
                    return not (1900 <= number <= 2099)
                matches=list(dict.fromkeys(m.group(1) for m in tokens if valid_match(m)))
                if len(matches)==1:
                    return 'LEGO ' + matches[0]
                if len(matches)>1:
                    return 'LEGO — più codici / bundle da verificare'
                return 'LEGO — set non identificato'
            subset['Codice set LEGO'] = subset.apply(lego_model, axis=1)
            # Names are keyed by verified set code. Retirement is displayed ONLY
            # when explicitly confirmed on the official LEGO Italy product page.
            lego_catalog = {
                '76294': ('X-Men: X-Mansion', 'disponibile'),
                '21325': ('Fabbro medievale', 'ritirato'),
                '10308': ('Natale nella strada principale', 'ritirato'),
                '21336': ('The Office', 'ritirato'),
                '10325': ('Baita alpina', 'ritirato'),
                '76178': ('Daily Bugle', 'ritirato'),
                '10267': ('Casa di pan di zenzero', 'ritirato'),
                '21341': ('Disney Hocus Pocus: cottage delle sorelle Sanderson', 'da verificare'),
                '75192': ('Millennium Falcon', 'da verificare'),
                '21351': ('Nightmare Before Christmas', 'da verificare'),
                '76218': ('Sanctum Sanctorum', 'da verificare'),
                '10300': ('Macchina del tempo di Ritorno al futuro', 'da verificare'),
                '21343': ('Villaggio vichingo', 'da verificare'),
                '21326': ('Winnie the Pooh', 'da verificare'),
            }
            @st.cache_data(ttl=3600, show_spinner=False)
            def load_lego_catalog():
                path = Path(__file__).resolve().parent / 'data/lego_catalog.db'
                if not path.exists():
                    return {}
                try:
                    with sqlite3.connect(f'file:{path.as_posix()}?mode=ro',uri=True,timeout=5) as cn:
                        return {code:(name,status) for code,name,status in cn.execute(
                            'SELECT code,name,status FROM lego_catalog WHERE name IS NOT NULL')}
                except sqlite3.Error:
                    return {}
            official_catalog = load_lego_catalog()
            def lego_label(value):
                found = re.fullmatch(r'LEGO (\d{3,7})', str(value))
                if not found:
                    return value
                code = found.group(1)
                entry = official_catalog.get(code) or lego_catalog.get(code)
                if entry is None:
                    return value
                name, state = entry
                symbol = '🔴 ' if state == 'ritirato' else ''
                return f'{symbol}LEGO {code} - {name}'
            subset['Codice set LEGO'] = subset['Codice set LEGO'].map(lego_label)
            st.caption('🔴 Prodotto ritirato secondo LEGO Italia (verifica 21/10/2026). '
                       'Senza icona = stato non confermato come ritirato; non equivale a disponibile.')

            # Distinguish condition separately from set identity and type.
            def lego_condition(row):
                title = str(row['title'] or '').casefold()
                kind = str(row['Tipo costruzione'])
                if kind == 'Set incompleti / pezzi mancanti':
                    return 'Incompleto / pezzi mancanti'
                if kind in ('Minifigure / personaggi', 'Lotti / pezzi misti',
                            'Accessori / scatole / ricambi', 'MOC / compatibili', 'Altre costruzioni'):
                    return 'Non applicabile / altro tipo'
                if re.search(r'\b(?:sigillat[oaie]|sealed|misb|new\s+in\s+box|nuovo\s+sigillato)\b', title):
                    return 'Nuovo / sigillato dichiarato'
                if re.search(r'\b(?:complet[oaie]|100%\s*complete|all\s+pieces|tutti\s+i\s+pezzi)\b', title):
                    return 'Usato completo dichiarato'
                return 'Completezza non verificabile'
            subset['Stato LEGO'] = subset.apply(lego_condition, axis=1)
            condition_choices = ['Tutti', 'Nuovo / sigillato dichiarato',
                'Usato completo dichiarato', 'Incompleto / pezzi mancanti',
                'Completezza non verificabile', 'Non applicabile / altro tipo']
            condition_choice = st.selectbox('Stato del set LEGO', condition_choices,
                help='Stato desunto esclusivamente dal titolo, non verificato fisicamente.')
            if kind_choice != 'Tutti':
                subset = subset[subset['Tipo costruzione'] == kind_choice].copy()
            if condition_choice != 'Tutti':
                subset = subset[subset['Stato LEGO'] == condition_choice].copy()
            if subset.empty:
                st.info('Nessun annuncio corrisponde ai filtri LEGO selezionati.')
                st.stop()

        st.subheader('🧩 Brand / famiglie / modelli')

        if export_id in ('20667','38250','139971','111422','175672'):
            def modello_commerciale(row):
                import re
                title = str(row['title'] or '')
                lower = title.lower()
                brand = str(row['Brand / Editore'] or 'Non identificato')
                model = str(row['Modello / Edizione'] or '').strip()
                # Codici TM con e senza spazi: stesso modello commerciale.
                tm = re.search(r'\b(?:bimby|thermomix|vorwerk).*?\btm\s*[- ]?\s*(31|5|6|7)\b|\btm\s*[- ]?\s*(31|5|6|7)\b',lower)
                if tm:
                    return 'Vorwerk Bimby TM' + (tm.group(1) or tm.group(2))
                if brand == 'KitchenAid':
                    if re.search(r'\bartisan\b|\b5ksm(?:125|150|175|185|195)\w*\b|\bksm150\w*\b',lower):
                        return 'KitchenAid Artisan Series 5'
                    if re.search(r'\bprofessional\s*5\s*plus\b',lower):
                        return 'KitchenAid Professional 5 Plus'
                    if re.search(r'\bk45ss\b',lower):
                        return 'KitchenAid Classic K45SS'
                if brand == 'Vitamix':
                    if re.search(r'\b5200\b|\bvm0103\b',lower):
                        return 'Vitamix 5200 / VM0103'
                if brand in ('Breville','Sage') and re.search(r'\bbes870\w*\b|barista express',lower):
                    return 'Breville / Sage Barista Express'
                if brand == 'Champion' and re.search(r'g5[-\s]?ng[-\s]?853s',lower):
                    return 'Champion G5-NG-853S'
                # Scarta etichette descrittive, colori e parole che non sono modelli.
                invalid = {'', 'modello non identificato', 'rosso', 'rossa', 'robot', 'attacchi',
                           'attacco', 'attachments', 'royal', 'slice', 'camp er', 'camper',
                           'robusto', 'ice cream', 'bianco', 'nera', 'nero', 'epicurean'}
                if model.casefold() in invalid:
                    from kitchen_model_extra import normalized_model
                    return normalized_model(row)
                if brand == 'Non identificato':
                    return 'Modello ' + model
                return brand + ' ' + model
            subset = subset.copy()
            subset['Modello commerciale'] = (subset['Modello / Edizione'] if export_id in ('38250','139971','111422','175672') else subset.apply(modello_commerciale, axis=1))
            group_level = 'Modello commerciale'

        elif export_id == '31388':
            # Compare like with like: camera model AND included lens configuration.
            # Never mix e.g. EOS 750D body only and EOS 750D with two lenses.
            subset = subset.copy()
            subset['Modello / configurazione'] = (
                subset['Modello / Edizione'].fillna('Modello da identificare').astype(str)
                + ' · ' + subset['Stato prodotto'].fillna('Dotazione non specificata').astype(str)
            )
            # Unknown models may be different products and must not share a median.
            unknown_camera = subset['Modello / Edizione'].fillna('').str.contains(
                'da identificare|da verificare|non identificat', case=False, regex=True
            )
            subset.loc[unknown_camera, 'Modello / configurazione'] += (
                ' [' + subset.loc[unknown_camera, 'item_id'].astype(str) + ']'
            )
            group_level = 'Modello / configurazione'
        elif export_id == '171485':
            subset = subset.copy()
            st.caption('📱 Modelli distinti per generazione, memoria e rete quando dichiarate. '
                       'La classificazione deriva dai titoli dei venditori e non certifica '
                       'lo stato o le specifiche effettive dei prodotti.')
            only_devices = st.checkbox(
                'Escludi accessori, lotti e dispositivi dichiarati guasti/bloccati',
                value=True, key='tablet_only_comparable')
            if only_devices:
                subset = subset[
                    ~subset['Stato prodotto'].fillna('').str.startswith('⚠️')
                ].copy()
            if subset.empty:
                st.info('Nessun dispositivo confrontabile con i filtri scelti.')
                st.stop()
            subset['Modello tablet/eReader'] = subset['Modello / Edizione'].fillna('Modello da identificare')
            unknown_tablet = subset['Modello tablet/eReader'].str.contains(
                r'da identificare|da verificare|non identificat|non specificat',
                case=False, regex=True)
            subset.loc[unknown_tablet, 'Modello tablet/eReader'] += (
                ' [' + subset.loc[unknown_tablet,'item_id'].astype(str) + ']'
            )
            if not only_devices:
                flagged = subset['Stato prodotto'].fillna('').str.startswith('⚠️')
                subset.loc[flagged, 'Modello tablet/eReader'] += (
                    ' · ' + subset.loc[flagged, 'Stato prodotto'].astype(str)
                    + ' [' + subset.loc[flagged,'item_id'].astype(str) + ']'
                )
            group_level = 'Modello tablet/eReader'
        elif export_id == '80053':
            # Every row is grouped by its actual identifiable monitor model,
            # not by generic panel type such as "Monitor gaming LCD".
            subset = subset.copy()
            def monitor_model_label(row):
                brand = str(row['Brand / Editore'])
                model = str(row['Modello / Edizione'])
                if row['Famiglia / Serie'] == 'Non è un monitor':
                    return 'Fuori categoria — ' + str(row['item_id'])
                if model not in ('Modello non identificato', 'Più modelli / lotto', 'nan', ''):
                    return (brand + ' ' if brand != 'Non identificato' else '') + model
                if model == 'Più modelli / lotto':
                    return 'Lotto di più monitor — ' + str(row['item_id'])
                # Retain seller title and item ID rather than falsely combining
                # different unknown models into one pseudo-model.
                return (brand + ' — modello da verificare: ' if brand != 'Non identificato'
                        else 'Monitor da identificare: ') + str(row['title'])[:85] + ' [' + str(row['item_id']) + ']'
            subset['Modello monitor'] = subset.apply(monitor_model_label, axis=1)
            group_level = 'Modello monitor'

        elif export_id == '183446':
            group_level = 'Codice set LEGO'
        else:
            group_level=st.radio('Raggruppa per', ['Famiglia / Serie','Brand / Editore','Modello / Edizione'],horizontal=True)
        # Demand ranking based on actual sale end dates, independent of initial listing dates.
        # Windows end at the current UTC day; do not include future-dated records.
        end_day = pd.Timestamp.now(tz='UTC').normalize()
        sold_dates = pd.to_datetime(subset['ended_at'], errors='coerce', utc=True)
        recent = subset.copy()
        recent['_sale_day'] = sold_dates
        recent['_7d'] = ((sold_dates >= end_day - pd.Timedelta(days=6)) & (sold_dates < end_day + pd.Timedelta(days=1))).astype(int)
        recent['_30d'] = ((sold_dates >= end_day - pd.Timedelta(days=29)) & (sold_dates < end_day + pd.Timedelta(days=1))).astype(int)
        recent['_prev30d'] = ((sold_dates >= end_day - pd.Timedelta(days=59)) & (sold_dates < end_day - pd.Timedelta(days=29))).astype(int)
        recent['_valid_date'] = sold_dates.notna().astype(int)
        recent['_seller'] = recent['seller'].fillna('').astype(str).str.strip().str.casefold()
        recent.loc[recent['_seller'].isin(['', 'none', 'nan', 'null']), '_seller'] = pd.NA
        suspect = recent['Modello / Edizione'].fillna('').astype(str).str.contains(
            r'non identificat|da identificare|non specificat|da verificare|più modelli',
            case=False,regex=True)
        suspect |= recent['Stato prodotto'].fillna('').astype(str).str.contains(
            r'guast|difett|ricamb|accessor|lotto|incomplet|blocc',
            case=False,regex=True)
        suspect |= recent['title'].fillna('').astype(str).str.contains(
            r'ricambi|solo scatola|box only|for parts|not working|lot of|lotto di|defekt',
            case=False,regex=True)
        if export_id == '31388':
            # Conservative buy-price suggestions only with a declared configuration.
            suspect |= recent['Stato prodotto'].fillna('').astype(str).eq('Dotazione non specificata')
        recent['_comparable'] = ~suspect
        recent['_comparable_price'] = recent['sold_price'].where(~suspect)
        # Fallback only for identifiable, non-defective items in the same model group.
        # Unknown camera configuration remains indicative, never a verified comparable.
        indicative_suspect = recent['Modello / Edizione'].fillna('').astype(str).str.contains(
            r'non identificat|da identificare|non specificat|da verificare|più modelli',
            case=False, regex=True)
        indicative_suspect |= recent['Stato prodotto'].fillna('').astype(str).str.contains(
            r'guast|difett|ricamb|accessor|lotto|incomplet|blocc',
            case=False, regex=True)
        indicative_suspect |= recent['title'].fillna('').astype(str).str.contains(
            r'ricambi|solo scatola|box only|for parts|not working|lot of|lotto di|defekt',
            case=False, regex=True)
        recent['_indicative_price'] = recent['sold_price'].where(~indicative_suspect)
        family_stats=(recent.groupby(group_level,dropna=False)
            .agg(Venduti=('item_id','size'), V7=('_7d','sum'), V30=('_30d','sum'),
                 Prev30=('_prev30d','sum'), Prezzo=('sold_price','median'),
                 Comparabili=('_comparable','sum'),
                 P25=('_comparable_price',lambda x:x.quantile(.25)),
                 Mediana_comparabili=('_comparable_price','median'),
                 Indicativi=('_indicative_price','count'),
                 P25_indicativo=('_indicative_price',lambda x:x.quantile(.25)),
                 Mediana_indicativa=('_indicative_price','median'),
                 Prezzo_min=('sold_price','min'), Prezzo_max=('sold_price','max'))
            .reset_index())
        display_group = 'Modello' if export_id in ('20667','38250','139971','111422','175672','183446','80053','31388','171485') else 'Famiglia'
        family_stats=family_stats.rename(columns={group_level:display_group})
        family_stats['Acquisto massimo €'] = family_stats['Mediana_comparabili'].apply(max_buy_price)
        family_stats['Acquisto prudente €'] = family_stats['P25'].apply(max_buy_price)
        verified = family_stats['Comparabili'] >= 5
        indicative = (~verified) & (family_stats['Indicativi'] >= 5)
        family_stats.loc[~verified, ['Acquisto massimo €','Acquisto prudente €']] = float('nan')
        family_stats.loc[indicative, 'Acquisto massimo €'] = family_stats.loc[
            indicative, 'Mediana_indicativa'].apply(max_buy_price)
        family_stats.loc[indicative, 'Acquisto prudente €'] = family_stats.loc[
            indicative, 'P25_indicativo'].apply(max_buy_price)
        family_stats['Tipo stima'] = 'Non disponibile'
        family_stats.loc[verified, 'Tipo stima'] = 'Verificata'
        family_stats.loc[indicative, 'Tipo stima'] = 'Indicativa · dotazione da verificare'
        family_stats['P25'] = family_stats['P25'].where(~indicative, family_stats['P25_indicativo'])
        family_stats['Rendimento %'] = ((family_stats['P25']-family_stats['Acquisto prudente €'])
            /family_stats['Acquisto prudente €']*100).where(family_stats['Acquisto prudente €']>0).round(1)
        family_stats['Affidabilità'] = family_stats['Comparabili'].apply(
            lambda n:'Alta' if n>=15 else ('Media' if n>=5 else 'Insufficiente'))
        family_stats['Indice opportunità'] = (
            55*family_stats['V30'].clip(upper=20)/20
            +25*family_stats['Rendimento %'].clip(lower=0,upper=60).fillna(0)/60
            +20*family_stats['Comparabili'].clip(upper=15)/15
        ).round().astype(int)
        # Indicative estimates must never rank as verified buying opportunities.
        family_stats.loc[family_stats['Comparabili']<5,'Indice opportunità']=0
        for price_column in ('Acquisto massimo €','Acquisto prudente €'):
            family_stats[price_column] = pd.to_numeric(family_stats[price_column],errors='coerce').replace([float('inf'),-float('inf')],float('nan')).apply(lambda v: int(10 * math.floor(float(v) / 10 + 0.5)) if pd.notna(v) else None)
        family_stats['⭐ Watchlist'] = family_stats[display_group].astype(str).isin(watchlist_names(str(subset['category_id'].iloc[0]))).map(
            {True: '⭐', False: ''})
        family_stats['Prezzo P25'] = family_stats['P25'].apply(lambda p:eur(p) if pd.notna(p) else 'N/D')
        family_stats['Prezzo']=family_stats['Prezzo'].apply(eur)
        family_stats['Prezzo minimo']=family_stats['Prezzo_min'].apply(eur)
        family_stats['Prezzo massimo']=family_stats['Prezzo_max'].apply(eur)
        family_stats['Tempo vendita']='N/D'
        # A full comparable 60-day history is not available for newly backfilled categories.
        # Earliest record alone does not prove continuous coverage, so label the comparison indicative.
        earliest = sold_dates.min()
        enough_history = pd.notna(earliest) and earliest <= end_day - pd.Timedelta(days=59)
        def trend_label(row):
            previous=int(row['Prev30'])
            current=int(row['V30'])
            if export_id == '183446' or not enough_history or previous == 0:
                return 'N/D'
            delta=(current-previous)*100.0/previous
            return ('+' if delta > 0 else '') + f'{delta:.1f}%'
        family_stats['Trend 30 gg']=family_stats.apply(trend_label,axis=1)
        if export_id == '183446':
            seller_rows = recent.dropna(subset=['_seller'])
            known_stats = seller_rows.groupby(group_level, dropna=False).agg(
                Venditori=('_seller','nunique'),
                Vendite_note=('_seller','size')).reset_index()
            top_seller = (seller_rows.groupby([group_level,'_seller'],dropna=False)
                .size().groupby(level=0).max().rename('Top_seller').reset_index())
            family_stats = family_stats.merge(known_stats,left_on=display_group,right_on=group_level,how='left')
            family_stats = family_stats.merge(top_seller,left_on=display_group,right_on=group_level,how='left')
            for col in ('Venditori','Vendite_note','Top_seller'):
                family_stats[col] = family_stats[col].fillna(0).astype(int)
            family_stats['Ripetute'] = (family_stats['Vendite_note'] - family_stats['Venditori']).clip(lower=0)
            family_stats['Concentrazione'] = family_stats.apply(
                lambda row: f"{100*row['Top_seller']/row['Vendite_note']:.0f}%"
                if row['Vendite_note'] else 'N/D',axis=1)
            # A missing seller is unknown, never a zero count.
            unknown_sellers = family_stats['Vendite_note'].eq(0)
            family_stats.loc[unknown_sellers, ['Venditori', 'Ripetute']] = 'N/D'



        leaders=family_stats[family_stats['V30']>=5].sort_values(['V30','V7','Venduti'],ascending=False)
        if not leaders.empty:
            leader=leaders.iloc[0]
            st.caption(f"🏆 Ultimi 30 gg: **{leader[display_group]}** · **{int(leader['V30'])} venduti** · mediana {leader['Prezzo']}")
        else:
            st.caption('ℹ️ Nessun modello con almeno 5 vendite negli ultimi 30 giorni: ordina per venduti totali o visualizza i gruppi disponibili.')

        ranking=st.selectbox('Classifica', ['🏆 Radar opportunità','Più venduti ultimi 30 gg','Più venduti ultimi 7 gg','Più venduti in totale'],key='ebay_recent_ranking',label_visibility='collapsed')
        ranking_col={'🏆 Radar opportunità':'Indice opportunità','Più venduti ultimi 30 gg':'V30','Più venduti ultimi 7 gg':'V7','Più venduti in totale':'Venduti'}[ranking]
        family_stats=family_stats.sort_values([ranking_col,'Venduti'],ascending=False,kind='stable').reset_index(drop=True)
        family_stats=family_stats.rename(columns={'V7':'Venduti 7 gg','V30':'Venduti 30 gg'})
        if export_id == '183446':
            cols = [display_group, 'Venduti', 'Venduti 30 gg', 'Venduti 7 gg', 'Prezzo', 'Prezzo P25', 'Acquisto massimo €', 'Acquisto prudente €', 'Comparabili', 'Tipo stima', 'Rendimento %', 'Affidabilità', 'Indice opportunità', '⭐ Watchlist']
        else:
            cols = [display_group, 'Venduti', 'Venduti 7 gg', 'Venduti 30 gg',
                    'Trend 30 gg', 'Prezzo', 'Prezzo P25', 'Acquisto massimo €', 'Acquisto prudente €', 'Comparabili', 'Tipo stima', 'Rendimento %', 'Affidabilità', 'Indice opportunità', '⭐ Watchlist', 'Prezzo minimo', 'Prezzo massimo', 'Tempo vendita']
        family_stats=family_stats[cols]
        # Only display labels change; all calculations retain their original keys.
        family_stats = family_stats.rename(columns={
            'Prezzo': 'Prezzo mediano',
            'Prezzo P25': 'Prezzo prudente (P25)',
        })

        # Compact toolbar instead of a tall stack before the ranking table.
        family_stats = family_stats.replace({None: float('nan')})
        left_filters, right_filters = st.columns([3, 2], gap='small')
        with left_filters:
            st.toggle('⭐ Solo watchlist', key='watchlist_only', value=False)
        with right_filters:
            st.caption('📊 Acquisti verificati: almeno 5 comparabili · Indicativi: almeno 5 annunci idonei ma con dotazione da verificare · margini 25/30/40 €')

        if st.session_state.get('watchlist_only', False):
            family_stats = family_stats[family_stats['⭐ Watchlist'] == '⭐'].copy()

        def price_highlight(v):
            try:
                return 'background-color:#dcfce7;color:#14532d;font-size:19px;font-weight:800' if 80<=float(v)<=130 else ''
            except (TypeError,ValueError):
                return ''
        # Default: six decision-driving columns; retain all other columns
        # in an optional detail view without changing the selected row IDs.
        compact_cols = [display_group, 'Venduti', 'Comparabili', 'Tipo stima',
                        'Prezzo mediano', 'Prezzo prudente (P25)',
                        'Acquisto massimo €', 'Acquisto prudente €']
        with st.expander('📊 Mostra statistiche complete', expanded=False):
            st.dataframe(family_stats, hide_index=True, width='stretch',
                         height=min(420, 60 + 35*len(family_stats)),
                         key='ebay_full_stats')
        visible_stats = family_stats[compact_cols].copy()
        highlight_cols = [c for c in ('Acquisto massimo €', 'Acquisto prudente €') if c in visible_stats.columns]
        styled_stats = visible_stats.style.format(na_rep='—')
        if highlight_cols:
            styled_stats = styled_stats.map(price_highlight, subset=highlight_cols)
        styled_stats = styled_stats.set_properties(
            subset=[display_group], **{'font-weight':'700','color':'#172b4d'}
        )
        state=st.dataframe(
            styled_stats, hide_index=True, width='stretch',
            height=min(660, 60 + 42*len(family_stats)),
            on_select='rerun', selection_mode='multi-row',
            key='ebay_family_table',
            column_config={display_group:st.column_config.TextColumn(display_group,width='large',help='Modello riconosciuto dagli annunci eBay'),
                           'Venduti':st.column_config.NumberColumn('Venduti totali',help='Numero complessivo di vendite registrate per questo modello o gruppo nel periodo disponibile.'),
                           'Comparabili':st.column_config.NumberColumn('Comparabili',help='Vendite dello stesso gruppo considerate affidabili per la stima verificata. Minimo 5.'),
                           'Tipo stima':st.column_config.TextColumn('Stima',help='Indicativa: configurazione non dichiarata o campione verificato insufficiente; controllare dotazione e singoli annunci prima di acquistare.'),
                           'Venduti 7 gg':st.column_config.NumberColumn('Venduti 7 gg'),
                           'Venduti 30 gg':st.column_config.NumberColumn('Venduti 30 gg'),
                           'Prezzo mediano':st.column_config.TextColumn('Mediana',width='small',help='Mediana di tutte le vendite registrate nel gruppo.'),
                           'Prezzo prudente (P25)':st.column_config.TextColumn('P25',width='small',help='P25 dei comparabili verificati, oppure degli annunci idonei quando la stima è indicativa.'),
                           'Acquisto massimo €':st.column_config.NumberColumn('Acquisto max',format='%.0f €',width='small',help='Da mediana comparabile o, se indicato, stima non verificata: controllare dotazione e condizioni'),
                           'Acquisto prudente €':st.column_config.NumberColumn('Acquisto P25',format='%.0f €',width='small',help='Prezzo massimo prudente di acquisto basato sul 25° percentile'),
                           'Rendimento %':st.column_config.NumberColumn('Rendimento %',format='%.1f%%')})
        with st.expander('⭐ Watchlist · gestisci', expanded=False):
            saved = watchlist_names(export_id)
            st.write('Modelli salvati:', ', '.join(sorted(saved)) if saved else 'Nessuno')
            editor_pw = os.getenv('EBAY_EDITOR_PASSWORD', '').strip()
            from hmac import compare_digest
            typed_pw = st.text_input('Password editor per modificare la watchlist', type='password', key='watchlist_password')
            if editor_pw and typed_pw and compare_digest(typed_pw, editor_pw):
                chosen_watch = st.selectbox('Modello / famiglia', family_stats[display_group].astype(str).tolist(), key='watchlist_model')
                wl_c1, wl_c2 = st.columns(2)
                if wl_c1.button('⭐ Aggiungi alla watchlist', key='watchlist_add'):
                    watchlist_change(export_id, chosen_watch, True)
                    st.rerun()
                if wl_c2.button('Rimuovi dalla watchlist', key='watchlist_remove'):
                    watchlist_change(export_id, chosen_watch, False)
                    st.rerun()
            elif typed_pw:
                st.error('Password editor non valida.')

        selected_indices=state.selection.rows
        chosen=family_stats.iloc[selected_indices][display_group].tolist() if selected_indices else []
        selected_data=subset[subset[group_level].isin(chosen)] if chosen else subset.iloc[0:0]
        if not chosen:
            st.info('👆 Seleziona uno o più modelli per vedere statistiche e annunci.' if export_id in ('20667','38250','139971','111422','175672') else '👆 Seleziona una o più famiglie nella tabella per vedere statistiche e annunci.')
        else:
            st.caption('📌 Selezionate: ' + ', '.join(chosen))
            c1,c2,c3,c4=st.columns(4)
            c1.metric('📦 Venduti',f'{len(selected_data):,}'.replace(',','.'))
            c2.metric('💰 Prezzo medio',eur(selected_data['sold_price'].mean()))
            c3.metric('🎯 Prezzo mediano',eur(selected_data['sold_price'].median()))
            c4.metric('🔥 Tempo mediano','N/D')
            st.caption('Per eBay il tempo di vendita non è disponibile senza la data iniziale dell’inserzione.')
            detail=selected_data.sort_values('ended_at',ascending=False).copy()
            st.download_button('📥 Esporta tutti gli annunci della famiglia (CSV)',
                data=detail.to_csv(index=False).encode('utf-8-sig'),
                file_name='venduti_ebay_famiglie.csv',mime='text/csv')
            st.subheader('📋 Annunci dei modelli selezionati' if export_id in ('20667','38250','139971','111422','175672') else '📋 Annunci delle famiglie selezionate')
            html_rows=[]
            for item in detail.head(100).itertuples(index=False):
                title=escape(str(item.title or 'Senza titolo'))
                url=str(item.url or '')
                p=urlparse(url)
                valid=p.scheme=='https' and bool(p.hostname) and (p.hostname=='ebay.it' or p.hostname.endswith('.ebay.it') or p.hostname=='ebay.com' or p.hostname.endswith('.ebay.com'))
                flag,flag_info=flag_for_location(getattr(item,'item_location',None), getattr(item,'category_id',None))
                badge_style = 'display:inline-flex;align-items:center;justify-content:center;line-height:1;margin-right:.18em;vertical-align:-0.08em;'
                if flag == "🇮🇹":
                    badge_style += 'font-size:1.38em;padding:.02em .18em;border-radius:.38em;background:linear-gradient(135deg,#dff6e5 0%,#ffffff 48%,#ffe3e3 100%);box-shadow:inset 0 0 0 1px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.10);'
                else:
                    badge_style += 'font-size:1.0em;'
                title = f'<span title="{escape(flag_info,quote=True)}" style="{badge_style}">{flag}</span> ' + title
                title_html=f'<a href="{escape(url,quote=True)}" target="_blank" rel="noopener noreferrer">{title}</a>' if valid else title
                image_url=str(item.image or '')
                img_parsed=urlparse(image_url)
                image_valid=img_parsed.scheme=='https' and bool(img_parsed.hostname)
                picture=f'<img src="{escape(image_url,quote=True)}" loading="lazy" alt="Foto annuncio">' if image_valid else '—'
                date=pd.to_datetime(item.ended_at,errors='coerce',utc=True)
                date_text=date.strftime('%d/%m/%Y') if pd.notna(date) else '—'
                html_rows.append(f'<tr><td>{picture}</td><td>{title_html}</td><td class="price">{eur(item.sold_price)}</td><td>—</td><td>{date_text}</td></tr>')
            st.markdown('<div class="mt-scroll"><table class="mt-sale-table"><thead><tr><th>Foto</th><th>Titolo</th><th>Prezzo</th><th>Venduto in</th><th>Rilevato venduto</th></tr></thead><tbody>'+''.join(html_rows)+'</tbody></table></div>',unsafe_allow_html=True)
            st.caption('Venduto in: N/D perché SoldComps non fornisce la data di pubblicazione. Rilevato venduto indica la data di chiusura eBay, non l’ora del rilevamento.')
            st.subheader('📈 Andamento prezzo')
            timeline=detail.copy()
            timeline['giorno']=pd.to_datetime(timeline['ended_at'],errors='coerce',utc=True).dt.date
            timeline=timeline.dropna(subset=['giorno','sold_price'])
            if not timeline.empty and timeline['giorno'].nunique()>1:
                daily=timeline.groupby('giorno',as_index=False)['sold_price'].median().rename(columns={'sold_price':'Prezzo mediano €'})
                st.line_chart(daily,x='giorno',y='Prezzo mediano €',width='stretch')
                st.caption('Mediana giornaliera dei prezzi degli annunci archiviati nella selezione.')
            else:
                st.info('Servono vendite in almeno due giorni diversi per mostrare un andamento dei prezzi.')
        st.caption('Le classifiche descrivono solo le vendite archiviate; trend non disponibile senza storico confrontabile. I prezzi di offerte accettate potrebbero essere indicativi.')
else:
    st.subheader('📦 Annunci venduti')
if section != '🏷️ Categorie' and not count:
    st.info('Nessun risultato per i filtri selezionati.')
elif section != '🏷️ Categorie':
    pages = (count + page_size - 1) // page_size
    current = st.number_input('Pagina', min_value=1, max_value=pages, value=1, step=1)
    order = {'Venduti più recenti':'ended_at DESC, first_seen DESC', 'Prezzo crescente':'sold_price ASC, ended_at DESC', 'Prezzo decrescente':'sold_price DESC, ended_at DESC'}[sort]
    with connect() as con:
        columns = {r[1] for r in con.execute('PRAGMA table_info(sales)')}
    start_col = 'posted_at' if 'posted_at' in columns else ('listed_at' if 'listed_at' in columns else None)
    select_location = ', item_location' if 'item_location' in columns else ', NULL AS item_location'
    select_start = ', ' + start_col + ' AS listed_at' if start_col else ', NULL AS listed_at'
    data = fetch('SELECT category_id, image, ended_at, title, sold_price, currency, url, COALESCE((SELECT name FROM categories WHERE category_id=sales.category_id), sales.category_id, \'Senza categoria\') AS category_name' + select_start + select_location + ' FROM sales WHERE ' + where_sql + ' ORDER BY ' + order + ' LIMIT ? OFFSET ?', tuple(params + [int(page_size), (int(current)-1)*page_size]))

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
        flag,flag_info=flag_for_location(item.get('item_location'), item.get('category_id'))
        badge_style = 'display:inline-flex;align-items:center;justify-content:center;line-height:1;margin-right:.18em;vertical-align:-0.08em;'
        if flag == "🇮🇹":
            badge_style += 'font-size:1.38em;padding:.02em .18em;border-radius:.38em;background:linear-gradient(135deg,#dff6e5 0%,#ffffff 48%,#ffe3e3 100%);box-shadow:inset 0 0 0 1px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.10);'
        else:
            badge_style += 'font-size:1.0em;'
        title = f'<span title="{escape(flag_info,quote=True)}" style="{badge_style}">{flag}</span> ' + title
        title_cell = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>' if link else title
        image_url = str(item['image']) if pd.notna(item['image']) else ''
        image_ok = urlparse(image_url).scheme == 'https'
        image_cell = f'<img src="{escape(image_url, quote=True)}" alt="Foto annuncio" loading="lazy">' if image_ok else '—'
        date_str = escape(str(item['ended_at'] or '—'))[:10]
        category_str = escape(str(item['category_name'] or 'Senza categoria'))
        price_str = eur(item['sold_price'])
        rows.append(f'<tr><td>{image_cell}</td><td>{title_cell}</td><td>{category_str}</td><td class="price">{price_str}</td><td>{date_str}</td><td>{sold_speed(item)}</td></tr>')
    html_table = ('<div class="mt-scroll"><table class="mt-sale-table"><thead><tr>'
                  '<th>Foto</th><th>Annuncio (clicca per aprire)</th><th>Categoria</th><th>Prezzo</th><th>Venduto il</th><th>🔥 Venduto in</th>'
                  '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')
    st.markdown(html_table, unsafe_allow_html=True)
    st.caption('🔥 Venduto in: calcolato solo quando è disponibile anche la data di pubblicazione. Al momento SoldComps ci restituisce la data di vendita, non la durata dell’inserzione.')
    st.caption(f'Pagina {current} di {pages} · {count:,} risultati · caricati solo {len(data)} annunci'.replace(',','.'))
    st.download_button('⬇️ Esporta questa pagina (CSV)', data=data.to_csv(index=False).encode('utf-8-sig'), file_name='venduti_ebay_pagina.csv', mime='text/csv')
    @st.cache_data(ttl=60, show_spinner=False)
    def export_all_sales(filter_sql, filter_params):
        return fetch(
            'SELECT category_id, item_id, title, sold_price, currency, ended_at, condition, url, image '
            'FROM sales WHERE ' + filter_sql + ' ORDER BY ended_at DESC, first_seen DESC',
            filter_params,
        )
    if count:
        all_sales=export_all_sales(where_sql, tuple(params))
        st.download_button(
            '📥 Esporta TUTTI i risultati filtrati (CSV) · ' + str(count) + ' annunci',
            data=all_sales.to_csv(index=False).encode('utf-8-sig'),
            file_name='venduti_ebay_tutti_risultati.csv',
            mime='text/csv',
            key='export_all_sold_results',
        )

with st.expander('📈 Andamento dei venduti archiviati', expanded=False):
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
