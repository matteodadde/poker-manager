# 🚀 DEPLOYMENT.md — Distribuzione di Poker Manager

Guida ufficiale e professionale per distribuire **Poker Manager** in produzione (o staging) utilizzando **Render.com** con runtime Python + PostgreSQL.

Questa guida è allineata con l'architettura reale dell’applicazione, con la struttura del progetto e con gli altri documenti tecnici.

---

# 📌 1. Panoramica

Poker Manager può essere distribuito facilmente grazie a:

* **Application Factory (`app_factory.py`)**
* **Configurazioni separate per ambiente (`config/production.py`)**
* **WSGI server Gunicorn**
* **Dipendenze consolidate in `requirements.txt`**

Render.com è la piattaforma consigliata per la prima pubblicazione, grazie a:

* Deploy automatici da GitHub
* Hosting Python gratuito
* Database PostgreSQL gratuito
* Supporto nativo per WSGI

---

# 📁 2. Requisiti

Prima di iniziare assicurati di avere:

* ✔️ Codice pulito e caricato su GitHub
* ✔️ File `requirements.txt` aggiornato
* ✔️ Configurazione `ProductionConfig` pronta
* ✔️ Presenza di `gunicorn` nel progetto
* ✔️ Nessun file sensibile nel repository (grazie a `.gitignore`)

---

# 🛠️ 3. Configurazione del Web Service su Render

1. Vai su **[https://dashboard.render.com](https://dashboard.render.com)**
2. Clicca **New → Web Service**
3. Concedi accesso a GitHub
4. Seleziona il repository **poker-manager**

### Configurazione consigliata

| Impostazione  | Valore                               |
| ------------- | ------------------------------------ |
| Runtime       | **Python 3.x**                       |
| Build Command | `pip install -r requirements.txt`    |
| Start Command | `gunicorn -b 0.0.0.0:10000 wsgi:app` |
| Branch        | `main` o `master`                    |
| Region        | EU (se presente)                     |
| Plan          | **Free**                             |

### 🔎 Nota importante

Assicurati che `gunicorn` sia nelle dipendenze:

```bash
pip install gunicorn
pip freeze > requirements.txt
```

---

# 🗄️ 4. Configurazione del Database PostgreSQL

1. Dashboard Render → **New → PostgreSQL**
2. Scegli il piano **Free**
3. Copia la stringa `DATABASE_URL`, simile a:

```
postgresql://USER:PASSWORD@HOST:PORT/DBNAME
```

Questa andrà inserita tra le variabili d'ambiente.

---

# 🔐 5. Variabili d’Ambiente Necessarie

Vai su Web Service → **Environment → Add Environment Variable**

Aggiungi:

```env
FLASK_ENV=production
DATABASE_URL=postgresql://...
SECRET_KEY=<chiave_generata>
```

Per generare una chiave sicura:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Variabili opzionali

```
LOG_LEVEL=INFO
ENABLE_PROFILING=false
```

---

# 🧱 6. Processo di Build e Start

Render farà automaticamente:

1. Clone del repository
2. Installazione dipendenze
3. Avvio server tramite Gunicorn
4. Esporre l’app su HTTPS

L’app sarà raggiungibile all’URL pubblico fornito da Render.

---

# 🎨 7. Gestione degli Assets Statici

Poker Manager usa:

* SCSS → compilato in CSS (via npm durante sviluppo)
* JS modulare
* Immagini dinamiche nella cartella `static/images/`

### Deploy su Render

Non serve configurazione extra:

* Flask serve i file statici direttamente
* Render gestisce i file così come sono presenti nella cartella `static/`

Se modifichi gli SCSS:

```bash
npm install
npm run build
```

Poi push → Render esegue un nuovo deploy.

---

# 🔄 8. Aggiornamento dell’App in Produzione

Ogni modifica al codice comporta un redeploy automatico.

```bash
git add .
git commit -m "feat: aggiornato dashboard leaderboard"
git push
```

Render rileva il push → ricostruisce l’app → nuova versione online.

---

# ⚠️ 9. Limitazioni del Piano Free di Render

* Idle dopo 15 minuti → prima richiesta lenta (cold start)
* Storage database limitato
* CPU non garantita

Per uptime continuo o carichi pesanti:

* valutare passaggio a VPS (es. Hetzner, DigitalOcean)
* configurazione avanzata prevista in un futuro `DEPLOYMENT_PRODUCTION.md`

---

# 🧪 10. Test prima del Deploy

Eseguire l’intera suite test:

```bash
pytest -vv
```

E assicurarsi che:

* l’app parte senza errori
* `ProductionConfig` non usa configurazioni locali
* il db viene caricato correttamente

---

# 🏁 11. Conclusione

Con questa configurazione, **Poker Manager** può essere distribuito facilmente e gratuitamente con Render.

La struttura modulare del progetto, la separazione degli ambienti e l’uso di Gunicorn garantiscono stabilità anche in produzione.

L’app è ora pronta per essere condivisa, testata e mostrata al mondo.
