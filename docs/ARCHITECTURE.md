# ARCHITECTURE

## 🧭 Panoramica Generale

Poker Manager è una web application strutturata in modo **modulare**, basata su **Flask**, organizzata secondo:

* **Application Factory pattern**
* **Blueprints separati per dominio** (players, tournaments, statistics, auth, main)
* **Modelli altamente modulari** separati per dominio
* **Struttura SCSS 7-1 professionalmente organizzata**
* **Logica statistiche isolata tramite mixin e `cached_property`**

L'obiettivo è garantire:

* manutenibilità
* separazione delle responsabilità
* performance tramite calcoli ottimizzati
* possibilità di espansione futura senza refactoring massivi

---

## 🏭 Application Factory

L'applicazione viene creata dinamicamente tramite la funzione `create_app` definita in **`app_factory.py`**.

```python
def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inizializzazione estensioni
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Registrazione Blueprint
    from app.routes.main import main_bp
    from app.routes.players import players_bp
    from app.routes.tournaments import tournaments_bp
    from app.routes.statistics import statistics_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(players_bp, url_prefix="/players")
    app.register_blueprint(tournaments_bp, url_prefix="/tournaments")
    app.register_blueprint(statistics_bp, url_prefix="/statistics")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
```

### 🎯 Perché l'Application Factory?

* Permette di creare app **diverse per ambiente** (dev / test / prod)
* Consente test completamente isolati
* Aumenta modularità e ordine della codebase
* Permette di registrare/isolamento dei Blueprint in modo pulito

---

## ⚙️ Configurazioni

Le configurazioni vivono in `app/config/` e seguono uno schema pulito e scalabile.

| File             | Scopo                                |
| ---------------- | ------------------------------------ |
| `base.py`        | Configurazione generale condivisa    |
| `development.py` | Modalità debug + logging esteso      |
| `testing.py`     | DB in memoria, test isolati e veloci |
| `production.py`  | Sicurezza, performance, niente debug |

In produzione viene usato **PostgreSQL**, configurato tramite `DATABASE_URL`.

---

## 🗄️ Modelli & Database Architecture

La struttura dei modelli è divisa per dominio:

```
app/models/
├── player/
├── tournament/
└── tournament_player/
```

Ogni dominio include:

* `base.py` → modello SQLAlchemy e relazioni
* `stats.py` → calcoli e logica statistica
* `validators.py` → validazione business logic

### 🔗 Relazioni Principali

* **Player 1 — N TournamentPlayer**
* **Tournament 1 — N TournamentPlayer**
* `TournamentPlayer` agisce come tabella pivot, con:

  * posizione
  * rebuy
  * prize
  * costi totali

### ⚡ Ottimizzazioni Database

* uso di `func`, `count(distinct ...)`, `case` per query performanti
* calcoli in SQL quando possibile
* parsing python-side solo per logiche avanzate

---

## 📦 Logica Statistiche

Le statistiche dei giocatori e dei tornei sono gestite tramite:

### **🔹 Mixin + Decorator Injection (`cached_property`)**

Questo pattern permette:

* calcoli eseguiti **una sola volta** per richiesta
* separazione totale tra dati e logica statistica
* performance ottimali su grandi dataset

Statistiche incluse:

* ROI, ITM rate, Win rate
* CPC, ABI, profitto medio
* Rebuy analytics (media, frequenza, ratio)
* Conversion Rate Win→ITM
* Streaks
* Breakdown costi
* Leaderboard metrics

---

## 🌐 Blueprint & Routing

Ogni sezione logica dell’app ha il suo Blueprint dedicato:

| Blueprint     | Path           | Cosa contiene                                   |
| ------------- | -------------- | ----------------------------------------------- |
| `main`        | `/`            | Home, pagine informative                        |
| `auth`        | `/auth`        | Login, logout, autenticazione                   |
| `players`     | `/players`     | CRUD giocatori, dettagli, statistiche personali |
| `tournaments` | `/tournaments` | Creazione/gestione tornei, risultati            |
| `statistics`  | `/statistics`  | Leaderboard, grafici, ranking                   |

Ogni blueprint include:

* `views.py`
* `forms.py`
* `utils.py`

---

## 🎨 Templates & Frontend Architecture

Organizzazione template:

```
app/templates/
├── layouts/ (layout globali)
├── components/ (navbar, footer, messaggi)
├── players/, tournaments/, statistics/ (pagine)
```

### 🌈 SCSS strutturato 7–1

```
static/scss/
├── base/
├── components/
├── layout/
├── pages/
└── main.scss
```

### 📜 JavaScript modulare

* `players.js`
* `tournaments.js`
* `leaderboard.js`
* `utils.js`

Approccio **Vanilla JS** senza framework per massima leggerezza.

---

## 🧪 Testing Architecture

Struttura test:

```
app/tests/
├── models/
├── routes/
├── integration/
└── performance/
```

I test usano **pytest**, fixture dedicate e DB isolato.

---

## 🔄 Flusso di esecuzione

1. `create_app()` crea l’istanza Flask
2. Inizializzazione estensioni
3. Registrazione Blueprint
4. Avvio tramite Gunicorn in produzione
5. Nginx → reverse proxy → Gunicorn → Flask

---

## ✅ Conclusione

L’architettura di Poker Manager è pensata per essere:

* modulare
* scalabile
* testabile
* pulita
* orientata a statistiche avanzate e prestazioni

Questo consente sviluppo rapido, refactoring semplice e possibilità di estensioni future senza complessità aggiuntiva.
