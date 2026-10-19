"""Venduti eBay: fast SQLite-backed Streamlit dashboard, category-wide collection unchanged."""
import os
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
from location_flags import flag_for_location

load_dotenv(Path(__file__).resolve().parent / '.env')
ACTIVE_CATEGORIES = ('141755', '63', '717', '233', '183446', '101376', '20667', '38250', '139971','111422')
st.set_page_config(page_title='Venduti eBay | MT TECH', page_icon='📚', layout='wide')
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
                    WHERE c.category_id IN ('141755','63','717','233','183446','101376','20667','38250','139971','111422')
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
    section = st.radio('Sezione', ['📦 Annunci venduti', '🏷️ Categorie'])
    category_opt = st.selectbox('Categoria', ['Tutte le categorie'] + list(names), format_func=lambda k: names.get(k, k))
    selected_category = None if category_opt == 'Tutte le categorie' else category_opt
    st.divider()
    st.header('🔎 Filtri')
    search = st.text_input('🔎 Cerca prodotto venduto', placeholder='Es. Mexico 86, Dylan Dog 1, Argentina 78…', help='Cerca tra gli annunci già presenti nel database, senza consumare crediti SoldComps.')
    period = st.selectbox('Periodo', ['Tutti', 'Ultimi 7 giorni', 'Ultimi 30 giorni', 'Ultimi 90 giorni', 'Ultimi 365 giorni'])
    condition = st.selectbox('Condizione', ['Tutte', 'Nuovo', 'Di seconda mano'])
    max_df = fetch("SELECT MAX(sold_price) hi FROM sales WHERE sold_price>=70 AND category_id IN ('141755','63','717','233','183446','101376','20667','38250','139971','111422')")
    highest = int(max(70, max_df.iloc[0]['hi'] or 70))
    price_low = st.number_input('Prezzo minimo visualizzato (€)', min_value=70, max_value=max(70,highest), value=70, step=10)
    price_high = st.number_input('Prezzo massimo visualizzato (€)', min_value=int(price_low), value=max(highest,int(price_low)), step=20)
    sort = st.selectbox('Ordina', ['Venduti più recenti', 'Prezzo crescente', 'Prezzo decrescente'])
    page_size = st.selectbox('Annunci per pagina', [25, 50, 100], index=1)
    if st.button('↻ Aggiorna dati', width='stretch'):
        fetch.clear()
        load_categories.clear()
        st.rerun()

where = ["category_id IN ('141755','63','717','233','183446','101376','20667','38250','139971','111422')", 'sold_price >= ?', 'sold_price >= ?', 'sold_price <= ?']
params = [70, float(price_low), float(price_high)]
if selected_category is not None:
    where.append('category_id = ?')
    params.append(selected_category)
if search.strip():
    # All words must occur, in any order. Accept common title variants.
    import re
    words = [w for w in re.split(r"[,;\\s]+", search.casefold().strip()) if w]
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
    def taxonomy_data():
        raw = fetch("""SELECT s.item_id, s.category_id, COALESCE(c.name,s.category_id) AS category_name,
                         s.title, s.sold_price, s.ended_at, s.url, s.image, s.item_location
                         FROM sales s LEFT JOIN categories c ON c.category_id=s.category_id
                         WHERE s.sold_price>=70 AND s.category_id IN ('141755','63','717','233','183446','101376','20667','38250','139971','111422')""")
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
            else:
                parsed.append((*classify(r.category_id, r.title), 'Non applicabile'))
        raw[['Brand / Editore','Famiglia / Serie','Modello / Edizione','Stato prodotto']] = pd.DataFrame(parsed,index=raw.index)
        # Promote repeated identifiable models to their own clickable family.
        # Keep the source family as a grouping key: comic issue 1 in one series
        # must never be mixed with issue 1 in another series.
        valid = (~raw['Modello / Edizione'].str.contains('non identificat',case=False,na=True)
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

    taxonomy = taxonomy_data()
    if selected_category is not None and not taxonomy.empty:
        taxonomy = taxonomy[taxonomy['category_id'].astype(str) == str(selected_category)]
    if taxonomy.empty:
        st.info('Nessun venduto disponibile per questa categoria.')
    else:
        categories = sorted(taxonomy['category_name'].dropna().unique().tolist())
        cat_name = st.selectbox('Categoria',categories,key='radar_category')
        subset = taxonomy[taxonomy['category_name']==cat_name]
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
        if export_id in ('20667','38250','139971','111422'):
            state_choice = st.selectbox(
                'Tipo prodotto', ['Tutti'] + sorted(subset['Stato prodotto'].dropna().unique().tolist()),
                help='Classificazione indicativa ricavata dal titolo; non sostituisce una verifica dell’annuncio.')
            if state_choice != 'Tutti':
                subset = subset[subset['Stato prodotto'] == state_choice]
            st.caption('Stato prodotto stimato dal titolo; il CSV completo contiene comunque tutti gli annunci e la relativa classificazione.')
        st.subheader('🧩 Brand / famiglie / modelli')
        st.caption('Seleziona una o più righe dalla tabella per analizzare le vendite. I raggruppamenti sono stimati dal titolo dell’annuncio.')
        if export_id in ('20667','38250','139971','111422'):
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
            subset['Modello commerciale'] = (subset['Modello / Edizione'] if export_id in ('38250','139971','111422') else subset.apply(modello_commerciale, axis=1))
            group_level = 'Modello commerciale'
            st.caption('Modelli commerciali riconosciuti e unificati (es. TM 5 = TM5). Quelli incerti restano separati; non vengono unificate le vendite.')
        else:
            group_level=st.radio('Raggruppa per', ['Famiglia / Serie','Brand / Editore','Modello / Edizione'],horizontal=True)
        family_stats=(subset.groupby(group_level,dropna=False)
                 .agg(Venduti=('item_id','size'), Prezzo_medio=('sold_price','mean'), Prezzo_mediano=('sold_price','median'))
                 .reset_index().sort_values('Venduti',ascending=False).reset_index(drop=True))
        family_stats=family_stats.rename(columns={group_level:('Modello' if export_id in ('20667','38250','139971','111422') else 'Famiglia'), 'Prezzo_medio':'Prezzo medio €','Prezzo_mediano':'Prezzo mediano €'})
        family_stats['Prezzo medio €']=family_stats['Prezzo medio €'].round(2)
        family_stats['Prezzo mediano €']=family_stats['Prezzo mediano €'].round(2)
        family_stats['Trend 30 gg']='N/D'
        family_stats['Tempo vendita']='N/D'
        display_group = 'Modello' if export_id in ('20667','38250','139971','111422') else 'Famiglia'
        family_stats=family_stats[[display_group,'Venduti','Trend 30 gg','Prezzo medio €','Prezzo mediano €','Tempo vendita']]
        state=st.dataframe(
            family_stats, hide_index=True, width='stretch',
            height=min(660, 60 + 42*len(family_stats)),
            on_select='rerun', selection_mode='multi-row',
            key='ebay_family_table',
            column_config={display_group:st.column_config.TextColumn(display_group,width='large'),
                           'Venduti':st.column_config.NumberColumn('Venduti'),
                           'Prezzo medio €':st.column_config.NumberColumn('Prezzo medio €',format='%.2f €'),
                           'Prezzo mediano €':st.column_config.NumberColumn('Prezzo mediano €',format='%.2f €')})
        selected_indices=state.selection.rows
        chosen=family_stats.iloc[selected_indices][display_group].tolist() if selected_indices else []
        selected_data=subset[subset[group_level].isin(chosen)] if chosen else subset.iloc[0:0]
        if not chosen:
            st.info('👆 Seleziona uno o più modelli per vedere statistiche e annunci.' if export_id in ('20667','38250','139971','111422') else '👆 Seleziona una o più famiglie nella tabella per vedere statistiche e annunci.')
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
            st.subheader('📋 Annunci dei modelli selezionati' if export_id in ('20667','38250','139971','111422') else '📋 Annunci delle famiglie selezionate')
            html_rows=[]
            for item in detail.head(100).itertuples(index=False):
                title=escape(str(item.title or 'Senza titolo'))
                url=str(item.url or '')
                p=urlparse(url)
                valid=p.scheme=='https' and bool(p.hostname) and (p.hostname=='ebay.it' or p.hostname.endswith('.ebay.it') or p.hostname=='ebay.com' or p.hostname.endswith('.ebay.com'))
                flag,flag_info=flag_for_location(getattr(item,'item_location',None))
                title = f'<span title="{escape(flag_info,quote=True)}">{flag}</span> ' + title
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
        st.caption('Trend e velocità non sono stimati da dati insufficienti; una volta raccolta una serie storica adeguata potremo calcolarli.')
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
    data = fetch('SELECT image, ended_at, title, sold_price, currency, url, COALESCE((SELECT name FROM categories WHERE category_id=sales.category_id), sales.category_id, \'Senza categoria\') AS category_name' + select_start + select_location + ' FROM sales WHERE ' + where_sql + ' ORDER BY ' + order + ' LIMIT ? OFFSET ?', tuple(params + [int(page_size), (int(current)-1)*page_size]))

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
        flag,flag_info=flag_for_location(item.get('item_location'))
        title = f'<span title="{escape(flag_info,quote=True)}">{flag}</span> ' + title
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
