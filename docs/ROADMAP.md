# 🛣️ ROADMAP.md — Evoluzione & Futuri Miglioramenti

Questa roadmap definisce l’evoluzione pianificata di **Poker Manager**, tenendo conto dell'uso reale dell’applicazione: un gruppo di amici che gioca regolarmente tornei e desidera un sistema affidabile, intuitivo e ricco di statistiche.

Gli obiettivi sono realistici, scalabili e coerenti con l’architettura attuale.

---

# 🎯 Visione Generale

Poker Manager diventerà un sistema completo per:

* gestire tornei live
* tracciare performance dettagliate dei giocatori
* fornire analisi statistiche avanzate
* offrire un'interfaccia moderna e piacevole

L’evoluzione sarà *incrementale* e focalizzata sulla qualità dell’esperienza.

---

# 🚀 1. Obiettivi a Breve Termine (1–3 mesi)

Funzionalità a impatto immediato, facili da implementare e utili alla community.

### ✔️ Miglioramento UI/UX

* Aggiunta di tooltip informativi nelle statistiche
* Ottimizzazione leaderboard (sorting migliorato, nuove metriche)
* Miglioramenti grafici per pagina player

### ✔️ Documentazione completa (già completata)

* API
* Architettura
* Testing
* Deployment
* Componenti

### 🔧 Rifiniture tecniche

* Cleanup codice JS multipagina
* Piccoli refactor dei modelli (type hinting, docstring)
* Miglioramento validazioni nei forms

### 📤 Miglioramento export dati

* Esportazione CSV risultati torneo
* Esportazione CSV leaderboard

---

# 🟨 2. Obiettivi a Medio Termine (3–6 mesi)

Funzionalità di qualità maggiore, pensate per rendere l’app un vero strumento completo.

## 🕒 2.1 Modalità *Live Tournament* (nuova sezione)

Feature principale richiesta dagli utenti.

### Funzionalità previste

* **Clock blinds integrato** con intervalli configurabili
* **Gestione livelli blinds** (small blind, big blind, ante)
* Timer dinamico e notifiche sonore
* Auto-log degli eventi (es. livello cambiato, pausa)
* Vista proiettore a schermo intero

## 🎮 2.2 Controllo torneo in tempo reale

* Numero giocatori restanti
* Stack medio calcolato automaticamente
* Bacheca eliminazioni
* Pulsante *“Next Blind Level”*
* Modalità pausa

## 📱 2.3 Supporto mobile migliorato

* Ottimizzazione layout responsivi
* Miglior interazione su smartphone

---

# 🟦 3. Obiettivi a Lungo Termine (6–12 mesi)

Funzionalità più ambiziose ma perfettamente integrabili.

## 📊 3.1 Sistema di statistiche avanzate

* Trendline multi-stagione
* Expected Value (EV) stimato
* Hall of Fame / records globali
* Analisi heatmap rebuy/ITM

## 🤝 3.2 Modalità *Teams*

* Creazione squadre
* Classifiche di squadra
* Punteggi combinati

## 🗃️ 3.3 Archiviazione stagioni / reset annuale

* Divisione in “stagioni” (2023, 2024…)
* Reset leaderboard annuale
* Archivio storico consultabile

## 🔐 3.4 Integrazione API pubblica (opzionale)

* Endpoint JSON per statistiche
* Token API per uso esterno

---

# 🧪 4. Qualità & Manutenzione Continua

Indipendentemente dalla roadmap temporale, verranno mantenuti:

### ✔️ Standard qualità codice

* test automatici completi per nuove feature
* CI locale con pytest
* refactor periodici

### ✔️ Manutenzione sicurezza

* aggiornamento dipendenze
* revisione configurazioni produzione

---

# 🧩 5. Feature Futuro Possibili (Non Prioritarie)

* Modalità bounty / knockout
* Generator bracket MTT
* Avatar personalizzabili
* Modalità cash game (tracking sessioni)

---

# 🏁 6. Conclusione

Questa roadmap definisce un percorso chiaro ed equilibrato:

* miglioramenti immediati
* nuove funzionalità utili nel contesto reale del gruppo di gioco
* espansioni future (live mode, statistiche avanzate, API)

Poker Manager è ora strutturato per crescere in modo solido e mantenibile mantenendo l’esperienza semplice e divertente per tutti gli utenti.
