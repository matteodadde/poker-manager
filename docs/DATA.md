# 📘 DATA MODEL — Poker Manager

Documentazione completa del modello dati per **Poker Manager**.
Include:

* Modelli ORM
* Relazioni
* Vincoli e validazioni
* Schema SQL
* Diagramma ER
* Esempi JSON
* Versioni compatibili SQL per PostgreSQL / MySQL

---

# 🧱 1. Panoramica Generale

Poker Manager utilizza **SQLAlchemy ORM** con:

* Application Factory
* Modelli separati per dominio
* Tabella pivot ricca `TournamentPlayer`
* Proprietà statistiche tramite `cached_property`
* Validators separati

Il database è progettato per:

* integrità
* performance
* possibilità di estensione futura

---

# 🧍‍♂️ 2. Modello `Player`

### Campi

| Campo        | Tipo                         | Note |
| ------------ | ---------------------------- | ---- |
| `id`         | Integer, PK                  |      |
| `nickname`   | String(50), unique, required |      |
| `avatar_url` | String(255), nullable        |      |
| `created_at` | DateTime, default now        |      |
| `updated_at` | DateTime, autoupdate         |      |

### Relazioni

* `tournament_players`: 1 → N
* `roles`: M → N

### Statistiche calcolate

Aggiunte da `stats.py`:

* `total_winnings`
* `total_spent`
* `net_profit`
* `roi`
* `win_rate`
* `itm_rate`
* `avg_profit_per_tournament`
* `avg_rebuy_per_tournament`
* `win_to_itm_ratio`
* `rebuy_frequency`

---

# 🏆 3. Modello `Tournament`

### Campi

| Campo            | Tipo                |
| ---------------- | ------------------- |
| `id`             | Integer, PK         |
| `name`           | String(100), unique |
| `date`           | Date                |
| `buy_in`         | Numeric(10,2)       |
| `starting_stack` | Integer             |
| `notes`          | Text                |

### Relazioni

* `tournament_players`: 1 → N

---

# 🔗 4. Modello `TournamentPlayer`

### PK Composita

* `player_id` (FK → Player.id)
* `tournament_id` (FK → Tournament.id)

### Campi

| Campo               | Tipo              |
| ------------------- | ----------------- |
| `posizione`         | Integer, nullable |
| `rebuy`             | Integer           |
| `rebuy_total_spent` | Numeric(10,2)     |
| `prize`             | Numeric(10,2)     |

### Validazioni

* rebuy ≥ 0
* prize ≥ 0
* posizione ≥ 1 o None
* coerenza rebuy × prezzi

### Statistiche

* `total_spent`
* `profit`

---

# 🛡 5. Ruoli (`Role`)

### Campi

| Campo         | Tipo           |
| ------------- | -------------- |
| `id`          | Integer, PK    |
| `name`        | String, unique |
| `description` | String         |

### Associazione

* Tabella: `roles_players`
* Many-to-many con Player

---

# 🌐 6. Relazioni del Database

```
               ┌──────────────┐
               │    Player     │
               └───────┬──────┘
                       │1
                       │
                       │N
              ┌────────▼──────────┐
              │  TournamentPlayer  │
              └────────┬──────────┘
                       │N
                       │
                       │1
               ┌───────▼────────┐
               │   Tournament    │
               └─────────────────┘

Player >───< Role
```

---

# 🧩 7. Schema SQL (PostgreSQL)

```sql
CREATE TABLE player (
  id SERIAL PRIMARY KEY,
  nickname VARCHAR(50) UNIQUE NOT NULL,
  avatar_url VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);

CREATE TABLE tournament (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  date DATE NOT NULL,
  buy_in NUMERIC(10,2) NOT NULL,
  starting_stack INTEGER,
  notes TEXT
);

CREATE TABLE tournament_player (
  player_id INTEGER REFERENCES player(id) ON DELETE CASCADE,
  tournament_id INTEGER REFERENCES tournament(id) ON DELETE CASCADE,
  posizione INTEGER,
  rebuy INTEGER DEFAULT 0,
  rebuy_total_spent NUMERIC(10,2),
  prize NUMERIC(10,2),
  PRIMARY KEY (player_id, tournament_id)
);

CREATE TABLE role (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,
  description VARCHAR(255)
);

CREATE TABLE roles_players (
  player_id INTEGER REFERENCES player(id) ON DELETE CASCADE,
  role_id INTEGER REFERENCES role(id) ON DELETE CASCADE,
  PRIMARY KEY (player_id, role_id)
);
```

---

# 🛢️ 8. Schema SQL (MySQL)

```sql
CREATE TABLE player (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nickname VARCHAR(50) UNIQUE NOT NULL,
  avatar_url VARCHAR(255),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE tournament (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  date DATE NOT NULL,
  buy_in DECIMAL(10,2) NOT NULL,
  starting_stack INT,
  notes TEXT
);

CREATE TABLE tournament_player (
  player_id INT,
  tournament_id INT,
  posizione INT,
  rebuy INT DEFAULT 0,
  rebuy_total_spent DECIMAL(10,2),
  prize DECIMAL(10,2),
  PRIMARY KEY (player_id, tournament_id),
  FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE,
  FOREIGN KEY (tournament_id) REFERENCES tournament(id) ON DELETE CASCADE
);

CREATE TABLE role (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,
  description VARCHAR(255)
);

CREATE TABLE roles_players (
  player_id INT,
  role_id INT,
  PRIMARY KEY (player_id, role_id),
  FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE
);
```

---

# 📦 9. Esempi JSON

## Player

```json
{
  "id": 1,
  "nickname": "Spado",
  "avatar_url": "/static/images/players/1.png",
  "created_at": "2025-02-10T18:11:00",
  "roles": ["user", "admin"]
}
```

## Tournament

```json
{
  "id": 12,
  "name": "Friday Poker Night",
  "date": "2025-02-01",
  "buy_in": 20.00,
  "starting_stack": 3000,
  "notes": "Torneo settimanale"
}
```

## TournamentPlayer

```json
{
  "player_id": 1,
  "tournament_id": 12,
  "posizione": 3,
  "rebuy": 1,
  "rebuy_total_spent": 20.00,
  "prize": 50.00,
  "total_spent": 40.00,
  "profit": 10.00
}
```

## Role

```json
{
  "id": 1,
  "name": "admin",
  "description": "Full permissions"
}
```

---

# 🚀 10. Considerazioni Finali

Il modello dati è:

* coerente
* normalizzato
* estensibile
* ottimizzato per statistiche complesse
* documentato per PostgreSQL e MySQL

Pronto per produzione e ulteriori estensioni.
