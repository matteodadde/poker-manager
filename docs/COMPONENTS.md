# 📦 COMPONENTS — Poker Manager

Documentazione ufficiale dei **componenti riutilizzabili** di Poker Manager.
Questo documento copre:

* Componenti UI (Jinja2 / HTML)
* Componenti JavaScript modulari
* Componenti SCSS (architettura 7-1)
* Risorse statiche condivise (icone, immagini, helpers)

L’obiettivo è fornire una panoramica chiara e professionale dei mattoni che compongono l’interfaccia utente e le funzioni interattive del progetto.

---

# 🎨 1. Componenti UI (Templates Jinja2)

I componenti HTML/Jinja2 risiedono in `app/templates/components/` e sono progettati per essere **riutilizzabili e indipendenti dal contesto**.

## 1.1 Navbar (`navbar.html`)

* Componente principale di navigazione
* Include link dinamici in base al login
* Rispetto del tema (chiaro/scuro)
* Utilizza Bootstrap 5 + icone BI

## 1.2 Footer (`footer.html`)

* Footer globale e leggero
* Incluso in ogni pagina tramite layout
* Zero logica, solo presentazione

## 1.3 Messages (`messages.html`)

* Componente per messaggi flash Flask
* Supporta:

  * success
  * warning
  * info
  * danger
* Auto-dismissing previsto dal CSS/JS

---

# 🧩 2. Layout & Template Generali

## 2.1 Layout principale (`layouts/base.html`)

* Includer di header, meta-tag, navbar, footer
* Import dinamico JavaScript per pagina
* Supporto tema chiaro/scuro centralizzato

## 2.2 Error Pages

In `templates/errors/`, tutte personalizzate:

* `400.html`
* `403.html`
* `404.html`
* `500.html`

---

# ⚙️ 3. Componenti JavaScript

Il JavaScript è modulare e organizzato per dominio.

Percorso: `static/js/`

## 3.1 `utils.js`

Utilità condivise:

* Funzioni helper per DOM
* Gestione tema
* Loader script dinamici
* Event dispatcher (es. themeChanged)

---

## 3.2 Charts (`charts/charts.js`)

Modulo avanzato che gestisce:

* Creazione dinamica grafici con Chart.js
* Fill rosso/verde basato sul profitto
* Gradiente dinamico
* Ridisegno grafici al cambio tema
* Eventi click sui punti → redirect al torneo relativo
* Supporto per mini-chart multipli

Include:

* `buildChartDataMap(playersData)`
* `createMiniCharts()`

---

## 3.3 Gestione Giocatori (`players/players.js`)

Funzionalità principali:

* Caricamento sicuro DataTables (con retry)
* Inizializzazione idempotente (evita doppie attivazioni)
* Modal dettagli giocatore generato dinamicamente
* Helpers debug globali

Caratteristiche tecniche avanzate:

* Distruzione sicura DataTables se già presente
* Riconfigurazione fallback dopo CDN lento
* Delegazione eventi per il modal

---

## 3.4 Leaderboard Dinamica (`statistics/leaderboard.js`)

Caratteristiche:

* Ordinamento tabella per qualsiasi statistica
* Formattazione automatica valori:

  * euro
  * percentuali
  * interi
* Evidenziazione del giocatore corrente
* Legend dinamica tramite dizionario descrizioni
* Aggiornamento header tabella

Usa DataTables + Bootstrap + jQuery.

---

## 3.5 Gestione Tornei (`tournaments/tournaments.js`)

Funzioni:

* Validazioni lato frontend
* Gestione interazioni tabellari
* Helper per forms

(Componente leggero ma coerente con l’architettura JS modulare).

---

# 🎀 4. Componenti SCSS (Architettura 7-1)

Gli stili sono organizzati in modo professionale, seguendo la struttura **7-1**:

```
static/scss/
├── base/
├── components/
├── layout/
├── pages/
└── main.scss
```

## 4.1 Cartella `base/`

* `_reset.scss` → reset CSS pulito
* `_variables.scss` → palette colori, spacing, font
* `_mixins.scss` → mixins globali
* `_functions.scss` → funzioni SCSS
* `_base.scss` → stili fondazione

## 4.2 Componenti (`components/`)

* `_grafico.scss` → stili per mini-chart & grafici
* `_index.scss` → componenti generici
* `_tornei.scss` → componenti correlati ai tornei

## 4.3 Layout (`layout/`)

* `_layout.scss` → griglie, container, spacing layout

## 4.4 Pagine (`pages/`)

* `_home.scss` → homepage
* `_leaderboard.scss` → pagina leaderboard
* `_players.scss` → pagina giocatori
* `_tournaments.scss` → pagina tornei

## 4.5 Entrypoint (`main.scss`)

Questo file compila tutto:

* importa variabili
* importa componenti
* genera `main.css`

---

# 🖼 5. Componenti Statici

## 5.1 Icone

* Bootstrap Icons (`fonts/bootstrap-icons/`)
* Usate in navbar, pulsanti, tooltip

## 5.2 Immagini

* Avatar giocatori (`images/players/`)
* Avatar placeholder (`default-avatar.png`)

## 5.3 File compilati

* `main.css` e `main.css.map`

---

# 🔄 6. Comportamenti Dinamici Chiave

### 6.1 Tema Dark/Light

* Gestito globalmente via `utils.js`
* Evento `themeChanged` per permettere ai grafici di ridisegnarsi
* Persistenza tramite `localStorage`

### 6.2 Mini Charts

* Creazione automatica al load della pagina
* Ridisegno al cambio tema
* Click su punto → redirect al torneo

### 6.3 Tabelle Dinamiche

* DataTables usato in modo idempotente e robusto
* Ottimizzazioni per evitare duplicazioni

---

# 🧭 7. Filosofia dei Componenti

Tutti i componenti seguono le linee guida:

* Modularità
* Indipendenza
* Riutilizzo
* Zero side-effects non necessari
* Codice leggibile e commentato
* Integrazione perfetta con Flask + Bootstrap

---

# ✅ 8. Conclusione

I componenti di Poker Manager — HTML, JS e SCSS — sono progettati per:

* essere estesi senza rompere nulla
* avere una struttura professionale
* garantire manutenibilità
* supportare statistiche complesse e UI dinamica

Pronti per sviluppi futuri, come:

* tabelloni live
* report esportabili
* dashboard amministrativa avanzata.
