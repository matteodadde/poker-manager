import pytest
from decimal import Decimal
from datetime import date, datetime
import sqlalchemy.exc
import logging
from app.models import Tournament, Player, TournamentPlayer
from app import db


@pytest.fixture
def test_data(db_session, sample_player, create_tournament):
    """Fixture helper per creare un player e un torneo di base per i test."""
    # Estrai il player dal dizionario della fixture
    player = sample_player["player"]
    tournament = create_tournament(buy_in=Decimal("100.00"))
    return player, tournament


def test_create_tp_and_repr(db_session, test_data, add_participation):
    """
    Testa la creazione base, le relazioni e il __repr__.
    """
    player, tournament = test_data

    tp = add_participation(
        player,
        tournament,
        posizione=1,
        rebuy=2,
        prize=Decimal("150.00"),
        rebuy_total_spent=Decimal("200.00"),
    )

    loaded = db_session.get(TournamentPlayer, (tournament.id, player.id))

    assert loaded is not None
    assert loaded.rebuy == 2
    assert loaded.posizione == 1
    assert loaded.prize == Decimal("150.00")
    assert loaded.rebuy_total_spent == Decimal("200.00")
    assert loaded.player.id == player.id
    assert loaded.tournament.id == tournament.id

    expected_repr = (
        f"<TournamentPlayer(t_id={tournament.id}, p_id={player.id}, "
        f"pos=1, rebuy=2, prize=150.00)>"
    )
    assert repr(loaded) == expected_repr


def test_update_rebuy_total_spent(db_session, test_data, add_participation):
    """
    Testa la logica del metodo update_rebuy_total_spent.
    """
    player, tournament = test_data

    tp = add_participation(player, tournament, rebuy=2)
    assert tp.rebuy_total_spent == Decimal("200.00")

    tp.update_rebuy_total_spent(use_half_price=True)
    db_session.commit()
    assert tp.rebuy_total_spent == Decimal("100.00")

    tp.update_rebuy_total_spent(use_half_price=False)
    db_session.commit()
    assert tp.rebuy_total_spent == Decimal("200.00")

    tp_detached = TournamentPlayer(player_id=player.id, rebuy=1)

    with pytest.raises(ValueError, match="Relazione 'tournament' non caricata"):
        tp_detached.update_rebuy_total_spent()


@pytest.mark.parametrize(
    "field, value, error_msg",
    [
        ("rebuy", "abc", "Il numero di rebuy deve essere un intero."),
        ("rebuy", -1, "Il numero di rebuy deve essere non negativo."),
        ("rebuy_total_spent", "abc", "numero decimale valido"),
        ("rebuy_total_spent", -10, "non può essere negativo"),
        ("posizione", "abc", "La posizione deve essere un intero."),
        # --- MODIFICA ---
        # Rimosso i caratteri speciali regex () e il punto .
        ("posizione", 0, "intero positivo"),
        ("posizione", -1, "intero positivo"),
        # --- FINE MODIFICA ---
        ("prize", "abc", "premio deve essere un numero non negativo valido."),
        ("prize", -10, "premio deve essere un numero non negativo valido."),
    ],
)
def test_tp_validators_simple_errors(test_data, field, value, error_msg):
    """
    Testa tutti i validatori per input errati (ValueError).
    """
    player, tournament = test_data

    data = {
        "player_id": player.id,
        "tournament_id": tournament.id,
    }

    if field != "rebuy_total_spent":
        data[field] = value

    if field == "rebuy_total_spent":
        with pytest.raises(ValueError, match=error_msg):
            tp = TournamentPlayer(
                player_id=player.id,
                tournament_id=tournament.id,
                rebuy_total_spent=value,
            )
            tp.tournament = tournament
            tp.rebuy_total_spent = value
    else:
        with pytest.raises(ValueError, match=error_msg):
            TournamentPlayer(**data)


def test_tp_validators_valid_nones_and_defaults(db_session, test_data):
    """
    Testa che i validatori gestiscano 'None' e applichino i default 0.
    """
    player, tournament = test_data

    tp = TournamentPlayer(
        player_id=player.id,
        tournament_id=tournament.id,
        rebuy=None,
        rebuy_total_spent=None,
        prize=None,
        posizione=None,
    )

    assert tp.rebuy == 0
    assert tp.rebuy_total_spent == Decimal("0.00")

    db_session.add(tp)
    db_session.commit()

    assert tp.prize is None
    assert tp.posizione is None


def test_validator_cross_validation_rebuy_spent(
    db_session, test_data, multiple_players, caplog
):
    """
    Testa la logica di validazione incrociata in validate_rebuy_total_spent.

    --- MODIFICA ---
    Usa 'multiple_players' per evitare conflitti di UNIQUE constraint.
    """
    # Crea 5 giocatori e 1 torneo
    players = multiple_players(5)
    _, tournament = test_data  # buy_in=100

    # --- Scenario 1: Errore (rebuy=0, spesa > 0) ---
    with pytest.raises(ValueError, match="speso per rebuy deve essere zero"):
        tp = TournamentPlayer(
            player_id=players[0].id,
            tournament_id=tournament.id,
            rebuy=0,
            rebuy_total_spent=Decimal("50.00"),
        )
        tp.tournament = tournament
        tp.rebuy_total_spent = Decimal("50.00")  # Attiva validatore
    # La sessione è pulita perché non c'è stato commit

    # --- Scenario 2: OK (rebuy=0, spesa=0) ---
    tp_ok = TournamentPlayer(
        player_id=players[1].id,
        tournament_id=tournament.id,
        rebuy=0,
        rebuy_total_spent=Decimal("0.00"),
    )
    tp_ok.tournament = tournament
    tp_ok.rebuy_total_spent = Decimal("0.00")
    db_session.add(tp_ok)  # Aggiungi alla sessione
    assert tp_ok.rebuy_total_spent == Decimal("0.00")

    # --- Scenario 3: OK (rebuy > 0, prezzo pieno) ---
    tp_full = TournamentPlayer(
        player_id=players[2].id,
        tournament_id=tournament.id,
        rebuy=2,
        rebuy_total_spent=Decimal("200.00"),
    )
    tp_full.tournament = tournament
    tp_full.rebuy_total_spent = Decimal("200.00")
    db_session.add(tp_full)  # Aggiungi alla sessione
    assert tp_full.rebuy_total_spent == Decimal("200.00")

    # --- Scenario 4: OK (rebuy > 0, metà prezzo) ---
    tp_half = TournamentPlayer(
        player_id=players[3].id,
        tournament_id=tournament.id,
        rebuy=2,
        rebuy_total_spent=Decimal("100.00"),
    )
    tp_half.tournament = tournament
    tp_half.rebuy_total_spent = Decimal("100.00")
    db_session.add(tp_half)  # Aggiungi alla sessione
    assert tp_half.rebuy_total_spent == Decimal("100.00")

    # --- Scenario 5: Warning (prezzo non standard) ---
    with caplog.at_level(logging.WARNING):
        tp_warn = TournamentPlayer(
            player_id=players[4].id,
            tournament_id=tournament.id,
            rebuy=2,
            rebuy_total_spent=Decimal("75.00"),
        )
        tp_warn.tournament = tournament
        tp_warn.rebuy_total_spent = Decimal("75.00")

        db_session.add(tp_warn)  # Aggiungi alla sessione

        # Ora fai il commit di tutti gli oggetti validi (ok, full, half, warn)
        db_session.add(tp)
        db_session.flush()

    assert "Costo rebuy (75.00) non standard" in caplog.text
    assert tp_warn.rebuy_total_spent == Decimal("75.00")
