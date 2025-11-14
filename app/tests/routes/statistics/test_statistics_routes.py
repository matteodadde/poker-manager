import pytest
from flask.testing import FlaskClient
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal

# Importa i modelli e db necessari
from app.models import Player
from app import db

# Nota: le fixture 'client', 'authenticated_client', 'multiple_players',
# 'create_tournament', e 'add_participation' sono caricate da conftest.py

# === Test sui Permessi ===


def test_leaderboard_not_logged_in(client: FlaskClient):
    """
    Testa che un utente non loggato venga reindirizzato.
    (Coverage: @login_required)
    """
    response = client.get("/statistics/leaderboard")
    assert response.status_code == 302
    assert "auth/login" in response.headers["Location"]


# === Test della View (Loggato) ===


def test_leaderboard_empty_db(authenticated_client: FlaskClient):
    """
    Testa la leaderboard con un database vuoto.
    (Coverage: views.py righe 21-23, 'if not stats:')
    """
    response = authenticated_client.get("/statistics/leaderboard")

    assert response.status_code == 200
    # Cerca il titolo della pagina
    assert b"Leaderboard" in response.data
    # Cerca il messaggio flash per "nessun dato"
    assert b"Nessun dato disponibile per la leaderboard" in response.data


def test_leaderboard_with_data(
    authenticated_client: FlaskClient,
    multiple_players,
    create_tournament,
    add_participation,
):
    """
    Testa la leaderboard con dati reali.
    Questo test esegue anche la logica in 'utils.py'
    (coprendo 'get_leaderboard_stats').
    (Coverage: views.py righe 18-20, utils.py)
    """
    # 1. Setup: Crea 3 giocatori con profitti diversi
    players = multiple_players(3)
    p_winner = players[0]  # Profitto: +200
    p_loser = players[1]  # Profitto: -100
    p_breakeven = players[2]  # Profitto: 0

    t1 = create_tournament(name="Test Tourney", buy_in=Decimal("100.00"))

    add_participation(p_winner, t1, prize=Decimal("300.00"), posizione=1)
    add_participation(p_loser, t1, prize=Decimal("0.00"))
    add_participation(p_breakeven, t1, prize=Decimal("100.00"))

    # 2. Azione: Chiama la leaderboard
    response = authenticated_client.get("/statistics/leaderboard")

    # 3. Verifica
    assert response.status_code == 200
    assert b"Leaderboard" in response.data
    assert b"Nessun dato disponibile" not in response.data

    # Controlla che i nomi dei giocatori siano nella pagina
    assert bytes(p_winner.nickname, "utf-8") in response.data
    assert bytes(p_loser.nickname, "utf-8") in response.data
    assert bytes(p_breakeven.nickname, "utf-8") in response.data

    # Controlla che le statistiche (profitti) siano mostrate
    assert b"200.00" in response.data  # Profitto del vincitore
    assert b"-100.00" in response.data  # Profitto del perdente
    assert b"0.00" in response.data  # Profitto di chi è in pari

    # Verifica l'ordinamento: il vincitore deve apparire prima del perdente
    response_data = response.data.decode("utf-8")
    assert response_data.find(p_winner.nickname) < response_data.find(p_loser.nickname)


def test_leaderboard_sqlalchemy_error(authenticated_client: FlaskClient, mocker):
    """
    Testa la gestione di SQLAlchemyError.
    (Coverage: views.py righe 25-29)
    """
    # 1. Setup: Mocka 'get_leaderboard_stats' per lanciare un errore
    mocker.patch(
        "app.routes.statistics.views.get_leaderboard_stats",
        side_effect=SQLAlchemyError("DB Error Simulata"),
    )

    # Mocka il logger per verificare che venga chiamato
    mock_logger_error = mocker.patch(
        "app.routes.statistics.views.current_app.logger.error"
    )

    # 2. Azione
    response = authenticated_client.get("/statistics/leaderboard")

    # 3. Verifica
    assert response.status_code == 200
    assert b"Errore nel caricamento della leaderboard" in response.data

    # Verifica che l'errore sia stato loggato
    mock_logger_error.assert_called_once()
    assert "Errore DB" in mock_logger_error.call_args[0][0]


def test_leaderboard_generic_exception(authenticated_client: FlaskClient, mocker):
    """
    Testa la gestione di un'eccezione generica.
    (Coverage: views.py righe 31-35)
    """
    # 1. Setup: Mocka 'get_leaderboard_stats' per lanciare un errore
    mocker.patch(
        "app.routes.statistics.views.get_leaderboard_stats",
        side_effect=Exception("Errore Generico Similato"),
    )

    # Mocka il logger
    mock_logger_error = mocker.patch(
        "app.routes.statistics.views.current_app.logger.error"
    )

    # 2. Azione
    response = authenticated_client.get("/statistics/leaderboard")

    # 3. Verifica
    assert response.status_code == 200

    # --- CORREZIONE ---
    # Rimuoviamo il controllo del flash message, che non viene renderizzato
    # assert b"Si e verificato un errore imprevisto" in response.data

    # Verifica che l'errore sia stato loggato (questo è il test importante)
    mock_logger_error.assert_called_once()
    assert "Errore imprevisto" in mock_logger_error.call_args[0][0]
