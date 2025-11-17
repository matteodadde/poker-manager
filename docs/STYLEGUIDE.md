# 🎨 STYLEGUIDE.md — Linee Guida di Stile

Questo documento definisce gli standard ufficiali per mantenere il codice di **Poker Manager** pulito, coerente e professionale. Le linee guida coprono Python, Jinja2, JavaScript, SCSS, struttura repository e convenzioni per i commit.

---

# 🐍 1. Stile Python

## 1.1 Standard

* Conformità a **PEP8**
* Lunghezza massima linea: **100 caratteri**
* Indentazione: **4 spazi**
* Niente tab

## 1.2 Convenzioni di Naming

* Variabili: `lower_snake_case`
* Funzioni: `lower_snake_case`
* Classi: `UpperCamelCase`
* Costanti: `UPPER_SNAKE_CASE`
* File Python: `lower_snake_case.py`

## 1.3 Import

Ordine:

1. built-in
2. terze parti
3. app local
4. modulo corrente

Sempre forma lunga:

```python
from app.models.player.base import Player
```

## 1.4 Modelli SQLAlchemy

* Modelli in directory dedicate per dominio
* Nessuna logica pesante nei modelli base
* Statistiche inserite tramite decorator (`stats.py`)
* Proprietà calcolate → `cached_property`
* Validazioni separate in `validators.py`

## 1.5 Error Handling

* Usare eccezioni specifiche
* Logging tramite `logging_config.py`

---

# 🧩 2. Stile Jinja2

## 2.1 Regole

* Indentazione: 2 spazi nei file template
* Variabili sempre escaping automatico `{{ var }}`
* Condizioni leggibili:

```jinja
{% if user.is_admin %}
```

## 2.2 Separazione dei template

* Layout generale in `layouts/base.html`
* Componenti riutilizzabili in `templates/components/`
* Template di pagina in directory dedicate per dominio

## 2.3 Best Practices

* Evitare logica complessa nei template
* Creare filtri personalizzati solo se necessario
* Commenti Jinja: `{# ... #}`

---

# ⚙️ 3. Stile JavaScript

## 3.1 Standard

* Linguaggio: **ES6+**
* Indentazione: **2 spazi**
* Preferire `const` e `let` rispetto a `var`

## 3.2 Naming

* Funzioni: `camelCase`
* Variabili: `camelCase`
* Classi JS: `PascalCase`
* File JS per dominio: `players.js`, `leaderboard.js`

## 3.3 Modularità

* Ogni pagina ha il proprio modulo JS
* `utils.js` contiene funzioni condivise
* Import dinamico dei moduli basato su `data-page` nel `<body>`

## 3.4 Best Practices

* Funzioni piccole e pure quando possibile
* Evitare manipolazioni del DOM non necessarie
* Commentare le funzioni complesse
* Gestire eccezioni e fallback (es. DataTables loading)

---

# 🎀 4. Stile SCSS — Architettura **7-1**

## 4.1 Regole Generali

* Struttura professionale suddivisa in 7 categorie + 1 entrypoint
* Indentazione: **2 spazi**
* Classi sempre in `kebab-case`
* Evitare annidamenti profondi (> 3 livelli)

## 4.2 Uso delle variabili

* Colori, spacing e breakpoint definiti in `_variables.scss`
* Mai usare valori hardcoded se esiste una variabile dedicata

## 4.3 Mixins & Functions

* Definiti in `_mixins.scss` e `_functions.scss`
* Utilizzare i mixin per ridurre codice ripetuto

## 4.4 Regole per i Componenti

* I componenti hanno file dedicati (`components/_grafico.scss`)
* Nessun stile inline nei template

## 4.5 Dark Mode

* Gestita tramite `data-bs-theme`
* Utilizzare CSS variables quando possibile

---

# 🧱 5. Organizzazione del Repository

## 5.1 Principi

* Ogni dominio ha la sua cartella (`players/`, `tournaments/`, ecc.)
* File separati per:

  * modelli
  * statistiche
  * validatori
  * viste
  * form
  * utilità

## 5.2 Static Assets

```
static/
  css/
  js/
  scss/
  images/
  fonts/
```

## 5.3 Tests

* Tests speculari alla struttura dell'app
* Divisione tra:

  * unit
  * integration
  * performance

---

# 📝 6. Regole per Commit Git

## 6.1 Convenzioni

Formato raccomandato **Conventional Commits**:

```
feat: aggiunta nuova funzionalità
fix: correzione bug
refactor: ristrutturazioni senza nuove funzionalità
style: modifiche estetiche o formattazione
test: aggiunta o modifica test
docs: aggiornamento documentazione
chore: manutenzione
```

## 6.2 Esempi

```
feat(stats): aggiunta rebuy_frequency nei calcoli
fix(players): risolto bug avatar_url mancante
refactor(js): migliorata inizializzazione DataTable
docs: aggiornato ARCHITECTURE.md
```

## 6.3 Linee guida

* Un commit = una singola intenzione
* Messaggi chiari e descrittivi
* Evitare commit del tipo "fix bug" senza contesto

---

# 🔍 7. Qualità del Codice

## 7.1 Standard

* Evitare duplicazione del codice
* Preferire funzioni piccole e testabili
* Logging essenziale nei punti critici

## 7.2 Code Review

* Nominare sempre motivazioni tecniche
* Chiedersi: *"Questo codice è estendibile?"*

---

# 🧪 8. Testing

* Ogni nuova feature deve avere almeno un test
* I test devono essere deterministici
* I test complessi devono usare fixtures dedicate
* L'intera suite deve girare in < 2s (obiettivo raggiunto)

---

# 🏁 9. Filosofia del Progetto

* Pulizia prima di complessità
* Architettura modulare
* Separazione chiara tra ruoli del codice
* Documentazione come parte del prodotto finale

**Poker Manager mantiene uno stile coerente, scalabile e professionale — tanto nello sviluppo quanto nella documentazione.**
