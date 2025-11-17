# 📘 API_REFERENCE.md — Riferimento Tecnico delle API

Documento tecnico completo con tutti gli endpoint principali di **Poker Manager**, organizzati per area funzionale.

✔️ Coerente con l'architettura reale dell'applicazione
✔️ Strutturato come una vera documentazione enterprise
✔️ Include: metodi, parametri, request/response, status code, esempi

---

# 📌 1. Convenzioni Generali

### Base URL

```
/  (root dell'app Flask)
```

### Formato richieste

* Le API sono principalmente orientate al browser (HTML + POST form)
* Alcuni endpoint possono restituire JSON

### Status code comuni

* **200 OK** → pagina o risposta valida
* **302 Redirect** → dopo POST form
* **400 Bad Request** → validazioni fallite
* **403 Forbidden** → permessi insufficienti
* **404 Not Found** → risorsa non esistente
* **500 Internal Server Error** → errori inaspettati

---

# 🔐 2. Autenticazione

## 2.1 Login

### `GET /login`

Restituisce il form di login.

### `POST /login`

Effettua l'autenticazione.

#### Params (form)

| Campo    | Tipo   | Obbligatorio | Descrizione       |
| -------- | ------ | ------------ | ----------------- |
| email    | string | sì           | Email registrata  |
| password | string | sì           | Password corretta |

#### Response

* `302 Redirect` verso dashboard
* `400` se credenziali non valide

---

## 2.2 Logout

### `GET /logout`

Termina la sessione corrente.

#### Response

* `302 Redirect` verso login

---

# 🧍‍♂️ 3. Players API

Gestione completa dei giocatori.

---

## 3.1 Lista giocatori

### `GET /players`

Restituisce la lista dei giocatori registrati.

#### Response

HTML (tabella giocatori).

---

## 3.2 Dettaglio giocatore

### `GET /players/<player_id>`

Mostra statistiche complete, grafici e partecipazioni.

#### Response

HTML + embed JSON per grafici e statistiche.

---

## 3.3 Creazione giocatore

### `GET /players/add`

Restituisce il form di creazione.

### `POST /players/add`

Crea un nuovo giocatore.

#### Params (form)

| Campo    | Tipo   | Obbligatorio | Note             |
| -------- | ------ | ------------ | ---------------- |
| nickname | string | sì           | unico            |
| avatar   | file   | no           | immagine PNG/JPG |

#### Response

* `302` → redirect alla lista
* errori validazione gestiti server-side

---

## 3.4 Modifica giocatore

### `GET /players/<id>/edit`

Mostra form di modifica.

### `POST /players/<id>/edit`

Aggiorna i dati del giocatore.

---

# 🎲 4. Tournaments API

Gestione tornei.

---

## 4.1 Lista tornei

### `GET /tournaments`

Restituisce l’elenco completo.

---

## 4.2 Dettaglio

### `GET /tournaments/<id>`

Mostra partecipanti, posizioni, premi, grafici.

---

## 4.3 Creazione torneo

### `GET /tournaments/add`

Form vuoto.

### `POST /tournaments/add`

Crea un torneo.

#### Params (form)

| Campo  | Tipo    | Obbligatorio |
| ------ | ------- | ------------ |
| name   | string  | sì           |
| buy_in | decimal | sì           |
| note   | string  | no           |

---

## 4.4 Modifica torneo

### `GET /tournaments/<id>/edit`

Form con dati precompilati.

### `POST /tournaments/<id>/edit`

Aggiorna i dettagli.

---

# 🔗 5. TournamentPlayer API

Endpoint che gestiscono le partecipazioni.

Queste operazioni sono incapsulate nelle view dei tornei.

---

## 5.1 Aggiunta partecipante

### `POST /tournaments/<id>/add_participation`

Aggiunge un player al torneo.

#### Params

| Campo     | Tipo    | Note            |
| --------- | ------- | --------------- |
| player_id | int     | ID giocatore    |
| posizione | int     | Optional        |
| rebuy     | int     | Numero rebuy    |
| prize     | decimal | premio ottenuto |

---

## 5.2 Aggiornamento partecipazione

### `POST /tournaments/<id>/update_participation`

Aggiorna posizione, premio e rebuy.

---

# 📊 6. Statistics API

## 6.1 Leaderboard

### `GET /statistics/leaderboard`

Restituisce la classifica globale con tutte le metriche aggregare.

#### Output (in-page JSON per JS)

Esempio:

```json
{
  "player_id": 4,
  "nickname": "Gero",
  "total_winnings": 380.0,
  "total_spent": 220.0,
  "roi": 72.7,
  "itm_rate": 64.2
}
```

#### Funzionalità

* sorting dinamico client-side
* statistiche avanzate calcolate con query SQL ottimizzate

---

# 🖼️ 7. Files statici & immagini

Non sono veri endpoint API, ma la documentazione tecnica li include per completezza.

### Esempi

* `/static/images/default-avatar.png`
* `/static/images/players/1_full.png`

---

# ⚠️ 8. Error API

Endpoint automatici gestiti da Flask.

### `GET /404`

Restituisce `404.html`.

### `GET /500`

Per errori interni (gestito automaticamente).

---

# 🧪 9. API Testing

Gli endpoint vengono testati in:

```
tests/routes/*
tests/integration/*
```

Esempio di test route:

```python
def test_players_list_status(client, auth):
    auth.login()
    resp = client.get('/players')
    assert resp.status_code == 200
```

---

# 🏁 10. Conclusione

Questa documentazione rappresenta la base tecnica completa delle API di Poker Manager.

Per dettagli architetturali:

* **ARCHITECTURE.md**
* **COMPONENTS.md**
* **DATA.md**

Per guida utente:

* **README.md**
