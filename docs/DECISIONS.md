# 🧭 DECISIONS.md — Architectural & Technical Decisions

Questo documento raccoglie le principali decisioni architetturali e tecniche che guidano lo sviluppo di **Poker Manager**. Ogni scelta è motivata da criteri di manutenibilità, performance, coerenza e scalabilità.

L’approccio segue lo stile ADR (Architecture Decision Record), ma in forma sintetica e pragmatica.

---

# 📌 1. Scelta del Framework Backend: **Flask**

**Decisione:** Utilizzare Flask come framework principale.

**Motivazioni:**

* leggero, estendibile e non opinionato
* perfetto per applicazioni modulari
* integrazione semplice con SQLAlchemy
* totale controllo sulla struttura del progetto
* routing chiaro e flessibile
* ideale per backend con rendering server-side (Jinja2)

**Alternative valutate:** FastAPI, Django

**Perché non scelte:**

* FastAPI eccellente per API-first, ma non necessario qui
* Django troppo vincolante per un'app con UI completamente personalizzata

---

# 📌 2. ORM: **SQLAlchemy**

**Decisione:** Utilizzare SQLAlchemy ORM con modelli separati per dominio.

**Motivazioni:**

* controlli avanzati del modello grazie a validators custom
* relazioni complesse gestite in modo elegante
* supporto nativo per PostgreSQL e MySQL
* integrazione naturale con Flask
* performance ottime, soprattutto tramite query aggregate

**Alternative:** raw SQL, Prisma, Tortoise ORM

---

# 📌 3. Struttura a Package Multiplo per i Modelli

**Decisione:** Separare i modelli in:

* `player/`
* `tournament/`
* `tournament_player/`

**Motivazioni:**

* massima leggibilità del codice
* riduce coupling tra moduli
* responsabilità ben chiare
* facilitazione test e mocking

---

# 📌 4. Stats Injection tramite `cached_property`

**Decisione:** Iniettare le statistiche nel modello Player tramite decorator e `cached_property`.

**Motivazioni:**

* evita di appesantire il modello base
* performance elevate: calcoli eseguiti una sola volta per request
* manutenibilità: facile aggiungere nuove metriche
* separazione tra *data layer* e *business logic*

**Alternative:** calcolo eager via query o mixin statici → meno flessibili.

---

# 📌 5. Tabella Pivot “TournamentPlayer” come Full Entity

**Decisione:** Rendere `TournamentPlayer` un modello completo e non una semplice association table.

**Motivazioni:**

* contiene dati chiave: posizione, rebuy, premi, profitto
* permette statistiche accurate storicizzate
* rende possibile estendere la logica (streaks, session stats, ecc.)

---

# 📌 6. Frontend: Server-side Rendering + JS modulare

**Decisione:** Usare Jinja2 come renderer primario e JavaScript modulare per funzionalità dinamiche.

**Motivazioni:**

* performance eccellenti su app con dataset medio-piccolo
* SEO friendly e leggerissimo
* JS usato solo dove necessario
* nessun framework frontend pesante richiesto (React/Vue)

**Risultato:** frontend snello, chiaro, responsive.

---

# 📌 7. DataTables per Liste Dinamiche

**Decisione:** Utilizzare DataTables per le liste di giocatori, tornei e leaderboard.

**Motivazioni:**

* sorting, pagination, search out-of-the-box
* integrazione perfetta con Bootstrap 5
* supporto per migliaia di righe senza problemi

**Alternative:** Tabulator, grid.js → più complesse senza necessità reale.

---

# 📌 8. Chart.js per le Statistiche Grafiche

**Decisione:** Chart.js come libreria grafica.

**Motivazioni:**

* look moderno e curato
* integrazione semplice con SCSS
* supporto per dark/light theme
* animazioni fluide
* ottimo rapporto leggibilità/complessità

---

# 📌 9. Architettura SCSS **7-1**

**Decisione:** organizzare gli stili tramite struttura professionale 7-1.

**Motivazioni:**

* separazione totale tra componenti, layout, utilità
* compilazione pulita del CSS finale
* coerenza tra pagine

---

# 📌 10. Gestione Tema Chiaro/Scuro (Dark Mode)

**Decisione:** gestione centralizzata tramite JS + CSS variables.

**Motivazioni:**

* completamente controllato da frontend
* persistenza tramite localStorage
* Chart.js ricalcola i colori dinamicamente via evento `themeChanged`

---

# 📌 11. Suite di Test Completa (Unit + Integration + Performance)

**Decisione:** Strutturare i test in cartelle parallele ai moduli reali.

**Motivazioni:**

* isolare casi d’uso critici
* copertura di every route e business logic
* performance testate tramite query predefinite

---

# 📌 12. Deployment via Docker

**Decisione:** container Docker con:

* app Flask
* database esterno
* WSGI (Gunicorn)

**Motivazioni:**

* ambiente riproducibile
* integrazione CI/CD futura
* scaling semplice

---

# 📌 13. Permessi tramite Ruoli (Role-Based Access Control)

**Decisione:** `Player` ↔ `Role` con many-to-many.

**Motivazioni:**

* permette privilegi amministrativi
* flessibile per futuri permessi granulari

---

# 🏁 Conclusione

Tutte le decisioni di Poker Manager sono state prese seguendo:

* chiarezza
* modularità
* scalabilità
* robustezza
* coerenza con un progetto professionale

Il risultato è una base solida, espandibile e adatta a crescita futura.
