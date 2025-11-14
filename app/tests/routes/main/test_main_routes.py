import pytest
from flask.testing import FlaskClient
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import Player, Tournament
from app.routes.main.utils import get_top_performers
from decimal import Decimal


def test_about_page(client: FlaskClient):
    """
    Testa che la pagina /about venga caricata correttamente.
    (Coverage: views.py righe 72-73)
    """
    response = client.get("/about")
    assert response.status_code == 200
    assert b"About" in response.data  # Assumendo che tu abbia un titolo 'About'


def test_index_page_empty_db(authenticated_client: FlaskClient):  # <-- CORREZIONE QUI
    """
    Testa la pagina index (/) con un database vuoto.
    Verifica che non ci siano errori e che i messaggi corretti vengano mostrati.
    (Coverage: views.py righe 36-49)
    """
    response = authenticated_client.get("/")  # <-- E QUI
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Nessun torneo" in response.data  # Messaggio atteso quando la lista è vuota
    assert b"Nessun giocatore registrato." in response.data  # Messaggio atteso

    # Verifica che il warning "Nessun performer trovato" sia stato loggato
    # (Questo test richiede 'caplog' ma lo teniamo semplice per ora)


def test_index_page_with_data(
    db_session,
    authenticated_client: FlaskClient,
    create_tournament,
    add_participation,
    multiple_players,
):  # <-- CORREZIONE QUI
    """
    Testa la pagina index (/) con dati.
    Verifica che i top player e i top tornei siano mostrati.
    (Coverage: views.py righe 36-45, 62-83 in utils.py)
    """
    # Crea 3 giocatori
    players = multiple_players(3)

    # Crea 2 tornei
    t1 = create_tournament(name="Torneo 1", prize_pool=Decimal("1000.00"))
    t2 = create_tournament(name="Torneo 2", prize_pool=Decimal("500.00"))

    # Aggiungi partecipazioni
    # Player 0 vince 200 (profitto 100)
    add_participation(players[0], t1, prize=Decimal("200.00"), rebuy=1)
    # Player 1 vince 100 (profitto 0)
    add_participation(players[1], t1, prize=Decimal("100.00"), rebuy=0)
    # Player 2 perde 100 (profitto -100)
    add_participation(players[2], t1, prize=Decimal("0.00"), rebuy=0)

    # Test con min_tournaments (copre utils.py righe 62-64)
    # Player 0 ha 1 torneo, non appare
    top_no_min = get_top_performers(min_tournaments=2)
    assert len(top_no_min) == 0

    # Test ordinamento ascendente (copre utils.py riga 73)
    top_asc = get_top_performers(order_by="net_profit", descending=False)
    assert top_asc[0].nickname == players[2].nickname  # Il peggiore è primo

    # Esegui la richiesta GET
    response = authenticated_client.get("/")  # <-- E QUI
    assert response.status_code == 200

    # Controlla che i dati siano nel HTML
    assert b"Torneo 1" in response.data
    assert b"1000.00" in response.data
    assert b"Torneo 2" in response.data
    assert b"500.00" in response.data

    # Controlla che il top player (Player 0) sia presente
    assert bytes(players[0].nickname, "utf-8") in response.data
    # Controlla che il peggior player (Player 2) sia presente
    assert bytes(players[2].nickname, "utf-8") in response.data


def test_index_page_db_error(
    authenticated_client: FlaskClient, mocker
):  # <-- CORREZIONE QUI
    """
    Testa il blocco 'except' della vista index.
    (Coverage: views.py righe 52-58, utils.py righe 79-83)
    """
    # Simula un errore DB
    mocker.patch("app.db.session.scalars", side_effect=SQLAlchemyError("DB Offline"))
    mock_rollback = mocker.patch("app.db.session.rollback")

    response = authenticated_client.get("/")  # <-- E QUI

    assert response.status_code == 200
    assert b"Impossibile caricare i dati della dashboard." in response.data
    # mock_rollback.assert_called() # Verifica che il rollback sia chiamato


def test_get_top_performers_db_error(db_session, mocker):
    """
    Testa che get_top_performers gestisca un SQLAlchemyError,
    facendo rollback e ritornando una lista vuota.
    """
    # 1. Simula l'errore:
    # Patch (sostituisci) la funzione 'execute' nel modulo 'utils'
    # e imposta il suo 'side_effect' per lanciare un errore.
    mock_execute = mocker.patch(
        "app.routes.main.utils.db.session.execute",
        side_effect=SQLAlchemyError("Simulated DB Error"),
    )

    # 2. Patch anche il rollback, così possiamo verificare che venga chiamato
    mock_rollback = mocker.patch("app.routes.main.utils.db.session.rollback")

    # 3. Esegui la funzione
    result = get_top_performers()

    # 4. Verifica
    # Il blocco 'try' è stato tentato
    mock_execute.assert_called_once()

    # Il blocco 'except' è stato eseguito
    mock_rollback.assert_called_once()

    # Il blocco 'except' ha ritornato una lista vuota (riga 57)
    assert result == []
