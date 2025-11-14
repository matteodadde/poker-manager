import pytest
import logging  # <-- Importa logging per il caplog
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError

# Importa i modelli necessari
from app.models import Player

# Importa le funzioni da testare
from app.routes.players.utils import (
    country_code_to_emoji,
    get_player_stats,
    get_top_performers,
)

# Nota: le fixture come db_session, multiple_players, create_tournament,
# e add_participation sono caricate automaticamente da conftest.py

# === Test per country_code_to_emoji ===


def test_country_code_to_emoji_valid():
    """Testa la conversione di codici validi."""
    assert country_code_to_emoji("IT") == "🇮🇹"
    assert country_code_to_emoji("us") == "🇺🇸"  # Test case-insensitivity
    assert country_code_to_emoji("FR") == "🇫🇷"


def test_country_code_to_emoji_invalid(mocker):  # <-- Aggiunto mocker
    """Testa input non validi che non dovrebbero generare emoji."""
    assert country_code_to_emoji(None) == ""  # Copre 'if not code:'
    assert country_code_to_emoji("") == ""

    # --- CORREZIONE: Mock della funzione di validazione ---
    # Per coprire la riga 'if not valid_code:', mockiamo il validatore
    # per fargli restituire None (o stringa vuota)
    mocker.patch("app.routes.players.utils.validate_country_code", return_value=None)
    assert country_code_to_emoji("XX") == ""  # Ora il validatore restituirà None

    # Questo test copre il blocco 'except ValueError' (riga 32-33)
    # (resettiamo il mock per questo test)
    mocker.patch(
        "app.routes.players.utils.validate_country_code",
        side_effect=ValueError("Test Error"),
    )
    assert country_code_to_emoji("Italia") == ""


# === Test per get_player_stats ===


def test_get_player_stats_empty(db_session):
    """
    Testa un giocatore nuovo senza statistiche.
    Verifica che tutti i valori siano 0 o 0.0, coprendo i 'None' check.
    """
    # Aggiungi i campi NOT NULL richiesti dal DB
    player = Player(
        nickname="Empty",
        email="empty@test.com",
        password_hash="hash",
        first_name="Test",  # Richiesto dal NOT NULL
        last_name="User",  # Richiesto dal NOT NULL
    )
    db_session.add(player)
    db_session.commit()

    stats = get_player_stats(player)

    # Confronta i tipi corretti
    assert stats["total_winnings"] == Decimal("0.00")
    assert stats["total_buyin_spent"] == Decimal("0.00")
    assert stats["total_rebuy_spent"] == Decimal("0.00")
    assert stats["total_spent"] == Decimal("0.00")
    assert stats["net_profit"] == Decimal("0.00")
    assert stats["num_tournaments"] == 0
    assert stats["num_wins"] == 0
    assert stats["win_rate"] == 0.0
    assert stats["in_the_money"] == 0
    assert stats["itm_rate"] == 0.0
    assert stats["num_rebuy"] == 0
    assert stats["avg_profit_per_tournament"] == Decimal("0.00")
    assert stats["avg_rebuy_per_tournament"] == 0.0
    assert stats["avg_prize_when_paid"] == Decimal("0.00")
    assert stats["win_to_itm_ratio"] == 0.0
    assert stats["num_zero_rebuy_tournaments"] == 0
    assert stats["country_emoji"] == ""


def test_get_player_stats_with_data(
    db_session, multiple_players, create_tournament, add_participation
):
    """
    Testa un giocatore con dati reali, verificando calcoli e formattazione.
    """
    # 1. Setup Dati
    player = multiple_players(1)[0]
    player.country = "IT"

    t1 = create_tournament(name="T1", buy_in=Decimal("100.00"))
    t2 = create_tournament(name="T2", buy_in=Decimal("50.00"))

    add_participation(player, t1, prize=Decimal("500.00"), rebuy=1, posizione=1)
    add_participation(player, t2, prize=Decimal("100.00"), rebuy=0, posizione=3)

    db_session.commit()

    # 2. Esegui la funzione
    stats = get_player_stats(player)

    # 3. Verifica (Confronta i tipi corretti)
    assert stats["total_winnings"] == Decimal("600.00")
    assert stats["total_buyin_spent"] == Decimal("150.00")
    assert stats["total_rebuy_spent"] == Decimal("100.00")
    assert stats["total_spent"] == Decimal("250.00")
    assert stats["net_profit"] == Decimal("350.00")

    assert stats["num_tournaments"] == 2
    assert stats["num_wins"] == 1
    assert stats["win_rate"] == Decimal("50.00")  # Calcolato come %
    assert stats["in_the_money"] == 2
    assert stats["itm_rate"] == Decimal("100.00")  # Calcolato come %
    assert stats["num_rebuy"] == 1
    assert stats["avg_profit_per_tournament"] == Decimal("175.00")
    assert stats["avg_rebuy_per_tournament"] == 0.5  # Questo è un float
    assert stats["avg_prize_when_paid"] == Decimal("300.00")

    # --- CORREZIONE: Questo è un float 0.5, non una % ---
    assert stats["win_to_itm_ratio"] == 0.5

    assert stats["num_zero_rebuy_tournaments"] == 1
    assert stats["country_emoji"] == "🇮🇹"


# === Test per get_top_performers ===


@pytest.fixture
def setup_performers(
    db_session, multiple_players, create_tournament, add_participation
):
    """
    Crea un set di dati complesso per testare ordinamenti e filtri.
    """
    players = multiple_players(4)
    p0, p1, p2, p3 = players

    t1 = create_tournament(name="T1")
    t2 = create_tournament(name="T2")
    t3 = create_tournament(name="T3")

    # P0: 3 tornei, 1 vittoria, +200 profitto
    add_participation(p0, t1, prize=Decimal("500.00"), posizione=1)  # +400
    add_participation(p0, t2, prize=Decimal("0.00"))  # -100
    add_participation(p0, t3, prize=Decimal("0.00"))  # -100

    # P1: 2 tornei, 0 vittorie, +300 profitto
    add_participation(p1, t1, prize=Decimal("200.00"), posizione=2)  # +100
    add_participation(p1, t2, prize=Decimal("300.00"), posizione=3)  # +200

    # P2: 1 torneo, 0 vittorie, -100 profitto
    add_participation(p2, t1, prize=Decimal("0.00"))  # -100

    # P3: 2 tornei, 0 vittorie, -200 profitto
    add_participation(p3, t1, prize=Decimal("0.00"))  # -100
    add_participation(p3, t2, prize=Decimal("0.00"))  # -100

    db_session.commit()
    return p0, p1, p2, p3


class TestGetTopPerformers:
    """Classe per raggruppare i test di get_top_performers"""

    def test_default_order_net_profit(self, setup_performers):
        """Testa l'ordinamento di default (net_profit, descending)."""
        p0, p1, p2, p3 = setup_performers

        # Ordine atteso: P1 (+300), P0 (+200), P2 (-100), P3 (-200)
        performers = get_top_performers()

        assert len(performers) == 4
        assert performers[0].id == p1.id
        assert performers[1].id == p0.id
        assert performers[2].id == p2.id
        assert performers[3].id == p3.id

    def test_limit(self, setup_performers):
        """Testa l'argomento 'limit'."""
        p0, p1, _, _ = setup_performers

        # Attesi solo i primi 2
        performers = get_top_performers(limit=2)

        assert len(performers) == 2
        assert performers[0].id == p1.id
        assert performers[1].id == p0.id

    def test_ascending(self, setup_performers):
        """Testa l'argomento 'descending=False'."""
        p0, p1, p2, p3 = setup_performers

        # Ordine inverso: P3 (-200), P2 (-100), P0 (+200), P1 (+300)
        performers = get_top_performers(descending=False)

        assert len(performers) == 4
        assert performers[0].id == p3.id
        assert performers[1].id == p2.id
        assert performers[2].id == p0.id
        assert performers[3].id == p1.id

    def test_min_tournaments(self, setup_performers):
        """Testa il filtro 'min_tournaments' (filtra P2)."""
        p0, p1, _, p3 = setup_performers

        # (Questo test ora passa perché abbiamo corretto il bug in utils.py)
        performers = get_top_performers(min_tournaments=2)

        assert len(performers) == 3
        assert performers[0].id == p1.id
        assert performers[1].id == p0.id
        assert performers[2].id == p3.id

    def test_order_by_other_field(self, setup_performers):
        """Testa l'ordinamento per 'num_wins'."""
        p0, p1, p2, p3 = setup_performers

        # Ordine atteso: P0 (1 vittoria), P1 (0), P2 (0), P3 (0)
        performers = get_top_performers(order_by="num_wins")

        assert len(performers) == 4
        assert performers[0].id == p0.id
        assert {p.id for p in performers[1:]} == {p1.id, p2.id, p3.id}

    def test_sqlalchemy_error(self, mocker, caplog):
        """Testa la gestione di SQLAlchemyError (copre righe 140-145)."""
        # Simula un errore DB
        mocker.patch(
            "app.db.session.scalars", side_effect=SQLAlchemyError("DB Offline")
        )
        mocker.patch("app.db.session.rollback")

        # --- CORREZIONE: Mocka il logger e controlla che sia chiamato ---
        mock_logger_error = mocker.patch(
            "app.routes.players.utils.current_app.logger.error"
        )

        performers = get_top_performers()

        assert performers == []  # Deve restituire lista vuota
        # Verifica che il logger sia stato chiamato
        mock_logger_error.assert_called_once()
        assert (
            "Errore DB" in mock_logger_error.call_args[0][0]
        )  # Controlla il messaggio

    def test_generic_exception(self, mocker):  # <-- Rimosso setup_performers
        """Testa un errore generico (copre righe 147-153)."""

        # --- CORREZIONE: Mocka il logger ---
        mock_logger_error = mocker.patch(
            "app.routes.players.utils.current_app.logger.error"
        )

        # --- CORREZIONE: Forza un'eccezione *dopo* la query ---
        # Mocka 'sorted' per far fallire la logica di ordinamento
        mocker.patch("builtins.sorted", side_effect=Exception("Sorting Error"))

        performers = get_top_performers()

        assert performers == []  # Deve restituire lista vuota
        # Verifica che il logger sia stato chiamato
        mock_logger_error.assert_called_once()
        assert (
            "Errore imprevisto" in mock_logger_error.call_args[0][0]
        )  # Controlla il messaggio
