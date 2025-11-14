# 📡 API.md — Panoramica delle API di Poker Manager

Questo documento descrive l’**interfaccia applicativa (API)** di Poker Manager in modo narrativo e comprensibile, offrendo una panoramica chiara degli endpoint principali, delle funzionalità fornite e dei flussi chiave dell’applicazione.

Per la documentazione tecnica dettagliata (parametri, codici HTTP, esempi JSON), fare riferimento a **API_REFERENCE.md**.

---

# 🧭 1. Introduzione

Poker Manager espone un insieme di endpoint HTTP che consentono:

* gestione di giocatori
* gestione di tornei
* registrazione delle partecipazioni
* visualizzazione di statistiche aggregate
* autenticazione e gestione sessioni

Le API sono principalmente orientate al browser, ma seguono una struttura REST-like che consente un uso anche programmatico.

---

# 🔐 2. Autenticazione & Sessione

L’app utilizza **sessione server-side con Flask-Login**.

## Endpoint principali

* `GET /login` → pagina login
* `POST /login` → validazione credenziali
* `GET /logout` → chiusura sessione

### Protezione risorse

Tutti gli endpoint di gestione (players, tournaments, statistics) richiedono:

* utente autenticato
* eventuali permessi aggiuntivi (es. ruolo admin)

---

# 🧍‍♂️ 3. API Giocatori (Players)

Gestisce anagrafiche, avatar e statistiche individuali.

## Endpoint principali

* `GET /players` → lista dei giocatori
* `GET /players/<id>` → pagina dettagli con grafici e statistiche
* `GET /players/add` → form creazione
* `POST /players/add` → salvataggio nuovo giocatore
* `GET /players/<id>/edit` → modifica giocatore
* `POST /players/<id>/edit` → aggiornamento

## Funzionalità

* caricamento avatar
* generazione grafici individuali
* statistiche derivate (ROI, ITM rate, profitto, rebuy frequency…)
* validazioni tramite `validators.py`

---

# 🎲 4. API Tornei (Tournaments)

Gestisce la creazione e amministrazione dei tornei.

## Endpoint principali

* `GET /tournaments` → elenco tornei
* `GET /tournaments/<id>` → dettaglio torneo
* `GET /tournaments/add` → aggiungi torneo
* `POST /tournaments/add` → salva
* `GET /tournaments/<id>/edit` → modifica torneo
* `POST /tournaments/<id>/edit` → aggiorna

## Funzionalità

* definizione buy-in
* gestione rebuy
* gestione posizione finale
* note e stack iniziale

---

# 🔗 5. API Partecipazioni (TournamentPlayer)

Rappresenta l’associazione ricca tra giocatore e torneo.

## Funzionalità principali

* assegnazione posizione
* inserimento premio
* calcolo spesa totale
* registrazione rebuy

Endpoint tipici (incapsulati nei form Tornei):

* `POST /tournaments/<id>/add_participation`
* `POST /tournaments/<id>/update_participation`

Il modello `TournamentPlayer` è responsabile delle statistiche di ogni partecipazione.

---

# 📊 6. API Statistiche (Leaderboard)

Endpoint centrale per confrontare i giocatori.

## Endpoint

* `GET /statistics/leaderboard` → pagina leaderboard dinamica

L’endpoint:

* aggrega centinaia di dati tramite query SQL ottimizzate
* costruisce una struttura JSON-like nella pagina
* permette sorting client-side per qualsiasi metrica

## Statistiche supportate

* profitto netto
* ROI
* ITM rate
* win rate
* ABI
* CPC
* rebuy frequency
* numero rebuy
* numero vittorie
* e molte altre

---

# 📦 7. API Utils (Filtri, Helpers, Componenti)

Non sono endpoint pubblici, ma funzioni che supportano il rendering e l’esperienza utente.

## Funzionalità incluse

* filtri Jinja2 personalizzati (`utils/filters.py`)
* funzioni decimal helper (`utils/decimal.py`)
* decorators (autorizzazione, logging)

---

# 🎨 8. API Frontend (JS Modules)

Ogni pagina carica dinamicamente il suo modulo JavaScript:

* `players.js` → gestione tabelle giocatori, modals
* `leaderboard.js` → sorting + formattazione statistiche
* `charts.js` → grafici individuali e mini-charts
* `tournaments.js` → validazioni form

L’import avviene da `base.html` tramite:

```html
<body data-page="players.list"> … </body>
```

Che individua quale modulo caricare.

---

# 🗄️ 9. Error Handling API

La webapp include pagine dedicate per errori:

* `400.html`
* `403.html`
* `404.html`
* `500.html`

E fallback controllati nelle views.

---

# 🚀 10. Use Case Principali

## 10.1 Creazione torneo + partecipazioni + leaderboard

1. Admin crea un torneo
2. Aggiunge partecipanti e risultati
3. L’endpoint leaderboard calcola le nuove statistiche globali

## 10.2 Aggiunta di un giocatore

1. Utente apre *Add Player*
2. Upload avatar
3. Dati validati → salvati
4. Visualizzazione grafici e performance

## 10.3 Consultazione del profilo giocatore

1. L’endpoint `/players/<id>` carica:

   * premi
   * win rate
   * grafici dinamici
   * partecipazioni

---

# 🏁 11. Conclusione

Questa API, sebbene orientata al rendering server-side, è progettata per essere:

* estensibile
* modulare
* facilmente esposta in formato JSON in futuro
* coerente con l’architettura generale dell’app

Per la documentazione dettagliata degli endpoint (payload, esempi, codici di risposta), consultare **API_REFERENCE.md**.
