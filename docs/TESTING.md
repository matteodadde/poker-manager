# 🧪 TESTING.md — Strategia e Struttura dei Test

Questo documento descrive la filosofia, la struttura e le linee guida della suite di test di **Poker Manager**, progettata per garantire affidabilità, regressione zero e qualità del codice.

La suite è completa e suddivisa in test **unitari**, **di integrazione**, **di performance** e **end-to-end leggero**.

---

# 📌 1. Filosofia della Suite di Test

La strategia dei test segue tre principi fondamentali:

### ✔️ Isolamento totale tra i test

Ogni test viene eseguito in un database pulito, grazie al sistema avanzato di cleanup in `conftest.py`.

### ✔️ Copertura completa delle funzionalità critiche

* modelli
* statistiche
* routing
* forms
* utils
* performance query

### ✔️ Riproducibilità

La suite deve:

* essere deterministica
* girare su qualsiasi macchina
* eseguire in meno di 3 secondi

---

# 🧱 2. Struttura della Suite di Test

Percorso completo:

```
/tests
├── commands/
├── integration/
├── models/
│   ├── player/
│   ├── roles/
│   ├── tournament/
│   └── tournament_player/
├── performance/
├── routes/
│   ├── auth/
│   ├── main/
│   ├── players/
│   ├── statistics/
│   └── tournaments/
├── utils/
└── conftest.py
```

## 2.1 Tests dei Modelli

I test sui modelli verificano:

* integrità dei dati
* default values
* validazioni custom
* relazioni ORM
* statistiche calcolate (es. ROI, ITM, rebuy frequency, ecc.)

### Cartelle

* `models/player/`
* `models/tournament/`
* `models/tournament_player/`
* `models/roles/`

Sono particolarmente completi i test delle statistiche del Player:

* `test_player_stats.py`
* `test_tournament_stats.py`
* `test_tournament_player_stats.py`

---

## 2.2 Tests di Routing

I test delle route verificano:

* risposte HTTP corrette
* autenticazione e protezione endpoint
* template caricati correttamente
* redirect previsti

Include:

* `/auth/` → login, logout, permessi
* `/players/` → CRUD giocatori
* `/tournaments/` → CRUD tornei
* `/statistics/leaderboard` → rendering + dati statistici

---

## 2.3 Tests di Integrazione

I test nella cartella `integration/` verificano workflow completi:

* creazione giocatore → login → accesso area protetta
* creazione torneo → partecipazione → calcolo statistiche → leaderboard
* test dei servizi integrati (es. aggregazioni DB)

Questi test garantiscono che l'app funzioni end-to-end.

---

## 2.4 Tests di Performance

Cartella: `performance/`

Qui si verificano:

* query aggregate su migliaia di record
* efficienza delle statistiche
* caching logico con `cached_property`

Esempi:

* `test_performance_queries.py` → simula carico elevato e verifica tempi di risposta.

---

## 2.5 Tests dei Comandi di Management

Cartella: `commands/`

Contiene test per:

* comandi CLI
* inizializzazione DB
* seed

Sono utili per garantire automazione CI/CD.

---

## 2.6 Tests dei Moduli Utils

Cartella: `utils/`

Include test specifici per funzionalità isolate:

* `test_decimal.py` → arrotondamenti
* `test_jinja_filters.py` → filtri utilizzati nei template (es. format money)

---

# ⚙️ 3. Fixture Avanzate in `conftest.py`

Il file `conftest.py` è estremamente avanzato e gestisce:

### ✔️ App Flask per test (scope session)

```python
@pytest.fixture(scope="session")
def app(): ...
```

### ✔️ Creazione/Distruzione database (session)

```python
@pytest.fixture(scope="session")
def db(app): ...
```

### ✔️ Sessione DB per ogni test con pulizia completa (function)

```python
@pytest.fixture(scope="function")
def db_session(db, app): ...
```

La pulizia avviene tramite:

```python
for table in reversed(_db.metadata.sorted_tables):
    _db.session.execute(table.delete())
```

Assicura database sempre vuoto tra test.

### ✔️ Client Flask automatico

```python
@pytest.fixture(scope="function")
def client(...):
```

### ✔️ Client autenticato

```python
@pytest.fixture
def authenticated_client(...):
```

### ✔️ Factory fixtures

* `create_tournament`
* `add_participation`
* `multiple_players`

Queste permettono di creare dati complessi con 1 riga.

---

# 🧪 4. Come Eseguire i Test

## 4.1 Comando standard

```bash
pytest
```

## 4.2 Verboso

```bash
pytest -vv
```

## 4.3 Solo un file

```bash
pytest tests/models/player/test_player_stats.py
```

## 4.4 Con coverage

```bash
pytest --cov=app --cov-report=term-missing
```

---

# 🔍 5. Linee Guida per Scrivere Nuovi Test

### 5.1 Ogni test deve essere indipendente

Usare sempre fixture `db_session`.

### 5.2 Nomi chiari

```
test_calcola_roi_correttamente()
```

### 5.3 Un test = un comportamento

Non raggruppare eccessi nello stesso test.

### 5.4 Arrange → Act → Assert

Seguire la struttura logica:

```python
# Arrange
player = ...

# Act
result = player.roi

# Assert
assert result == Decimal("50.00")
```

### 5.5 Coprire edge cases

Esempi importanti:

* 0 tornei
* rebuy nulli
* premi mancanti
* divisioni per zero

---

# 🧵 6. Obiettivi della Suite

La suite garantisce:

* stabilità del codice
* regressioni zero
* sviluppo rapido senza paura
* qualità della logica statistica
* solidità delle query aggregate

---

# 🏁 7. Conclusione

La suite test di **Poker Manager** è progettata come una vera suite enterprise:

* completa
* modulare
* veloce
* affidabile
* con fixture professionali

Rappresenta uno dei punti di forza principali dell’intero progetto e assicura che ogni modifica al codice sia sicura e prevedibile.
