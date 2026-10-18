# Venduti eBay — monitor categoria 141755

Monitora venduti pubblici della categoria **Album di figurine** su eBay Italia tramite l'endpoint `GET /v1/scrape/category` di SoldComps, senza parole chiave. Archivia in SQLite, dashboard Streamlit e notifiche Telegram opzionali. I dati non sono ancora stati verificati con una chiave API reale.

## Installazione sulla VPS

```bash
mkdir -p /opt/venduti-ebay
cd /opt/venduti-ebay
# Copia qui il contenuto di questo progetto
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
nano .env
.venv/bin/python collector.py
.venv/bin/streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8505
```

Apri la dashboard tramite un reverse proxy Nginx con autenticazione: **non esporre direttamente la porta 8505 a Internet**.

## Pianificare le raccolte ogni 30 minuti

```cron
*/30 * * * * cd /opt/venduti-ebay && /usr/bin/flock -n /tmp/venduti-ebay.lock /opt/venduti-ebay/.venv/bin/python collector.py >> /opt/venduti-ebay/collector.log 2>&1
```

Inserisci questa riga con `crontab -e`. Non avviare il cron finché il primo controllo non funziona correttamente.

## API

1. Registrati su https://sold-comps.com/ e apri la dashboard per creare la chiave `sc_...`.
2. Inseriscila **solo sulla VPS** nel file `.env` (non inviarla in chat e non committarla su GitHub).
3. Il progetto manda sempre `X-Credit-Source: subscription-only`, quindi **non consuma crediti acquistati**.
4. La quota gratuita documentata è 100 richieste per ciclo mensile; un controllo ogni 30 minuti è circa 1440 richieste/30 giorni, quindi per la frequenza continua servirà un piano maggiore oppure ripensare la frequenza.
5. Un controllo = una pagina fino a 240 inserzioni. La copertura dipende dal volume: il monitor può perdere vendite se si aggiungono oltre 240 risultati fra controlli. Aumenta MAX_PAGES_PER_RUN solo dopo aver stimato il consumo.
6. La prima raccolta crea la base storica senza notifiche; dai controlli successivi notifica i nuovi ID.
7. La raccolta registra il prezzo visualizzato nell'inserzione: per le proposte d'acquisto accettate potrebbe non essere il prezzo realmente pagato.

**Sicurezza:** non incollare la chiave API o il token Telegram in chat, non aggiungere `.env` a GitHub, usa HTTPS e proteggi la dashboard.
