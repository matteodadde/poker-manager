# Poker Manager

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Tests](https://img.shields.io/badge/tests-100%25-brightgreen.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

Poker Manager è un’applicazione web completa per la gestione di partite e tornei di poker tra amici, circoli o piccole associazioni.
Permette di registrare giocatori, tracciare tornei, calcolare statistiche avanzate e produrre leaderboard dinamiche.

È sviluppato principalmente per **sviluppatori** interessati ad approfondire Flask, architetture modulari, query ottimizzate e tecniche avanzate di stat analysis.

---

# 🚀 Funzionalità Principali

### 👤 **Gestione Giocatori**

* Creazione / modifica profilo
* Avatar dinamici
* Statistiche personali complete
* Pagina dettaglio giocatore con grafici

### 🎲 **Gestione Tornei**

* Aggiunta, modifica e cancellazione tornei
* Gestione partecipanti e posizionamenti
* Buy-in, rebuy e premi gestiti automaticamente
* Calcolo automatico di profitti, ranking, ABI, ecc.

### 📊 **Statistiche Avanzate**

* ROI (%)
* ITM Rate (%)
* Win Rate (%)
* Rebuy analytics (media, frequenza, rapporto)
* CPC (Cost Per Cash)
* Conversion Rate Win/ITM
* Profitto medio, premio medio, ABI
* Leaderboard dinamica filtrabile

### 🏆 **Leaderboard Dinamica**

* Ordinabile per qualsiasi statistica
* Descrizioni automatiche
* Highlight del giocatore corrente
* Supporto per ranking avanzati

### 🔒 **Autenticazione & Ruoli**

* Login sicuro
* Ruoli (admin / user)
* Protezione completa delle route

### 🎨 **Frontend Moderno**

* SCSS modulare (architettura 7-1)
* Componenti Jinja2 riutilizzabili
* Grafici dinamici
* Interfaccia responsive

---

# 🛠️ Stack Tecnologico

| Componente    | Tecnologia             |
| ------------- | ---------------------- |
| Backend       | Python 3.x, Flask      |
| Templating    | Jinja2                 |
| Frontend      | SCSS + Vanilla JS      |
| Database      | PostgreSQL             |
| Deploy        | Docker, Docker Compose |
| Server App    | Gunicorn               |
| Reverse Proxy | Nginx                  |

---

# 📁 Struttura del Progetto

Il progetto segue una struttura pulita in **Blueprint** e moduli separati per modelli, form, views, statistiche, validatori, statici e template.

La struttura completa è consultabile in `docs/ARCHITECTURE.md`.

---

# 🧰 Requisiti

* Python **3.10+**
* PostgreSQL **14+**
* Node.js **(se rigeneri SCSS)**
* Docker (per il deployment o sviluppo isolato)

---

# ⚙️ Installazione Locale (Sviluppo)

```bash
git clone <repo-url>
cd poker-manager

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Variabili ambiente richieste

```bash
export FLASK_ENV=development
export DATABASE_URL="postgresql://user:password@localhost:5432/pokerdb"
```

### Avvio dell'app

```bash
flask run
```

---

# 🧪 Testing

Il progetto include:

* Test unitari
* Test di integrazione
* Test performance
* Fixtures condivise

Esegui tutto con:

```bash
pytest -q
```

---

# 🐳 Deployment (Docker)

Il progetto è pronto per la produzione via Docker.

### Avvio completo

```bash
docker-compose up --build -d
```

### Componenti inclusi

* app Flask via Gunicorn
* database PostgreSQL
* reverse proxy Nginx
* rete interna
* persistenza dei dati

La guida completa è in:
📄 **`docs/DEPLOYMENT.md`**

---

# 🌐 Mini-Documentazione API

La documentazione API completa è in:

📄 `docs/API.md`
📄 `docs/API_REFERENCE.md`

Nel README inseriamo solo una panoramica:

### `/players/`

* GET lista giocatori
* GET dettaglio
* POST nuovo giocatore

### `/tournaments/`

* GET lista tornei
* POST creare torneo
* POST assegnare premi / posizioni

### `/statistics/leaderboard`

* GET leaderboard dinamica
* Opzioni di sorting

---

# 🧭 Roadmap (estratto)

La roadmap completa è in `docs/ROADMAP.md`.

Le prossime feature previste:

* Grafici avanzati su pagina giocatore
* Modalità dark mode opzionale
* API REST documentate con Swagger/OpenAPI
* Dashboard amministrativa
* Sistema notifiche email
* Possibile export CSV/Excel delle statistiche

---

# ⚖️ Licenza

Licenza: **MIT**
Usa, modifica e redistribuisci liberamente.

---

# ⚠️ Disclaimer

Questo progetto **non è affiliato con nessuna piattaforma di poker**, casinò o brand registrato.
È destinato esclusivamente a uso **privato, didattico o amatoriale**.

---

**Made with ❤️ … e probabilmente qualche bad beat.**
