import pytest
from decimal import Decimal
from app.models.tournament_player.stats import add_stats_properties
from app.models.tournament_player.base import TournamentPlayer
from app.models.tournament.base import Tournament  # Importa Tournament


@pytest.fixture
def sample_tournament_player(db_session, sample_player, sample_tournament):
    """
    Fixture che crea una partecipazione di base (TP) e la restituisce.
    """
    # Applica le @cached_property alla classe
    add_stats_properties(TournamentPlayer)

    # --- CORREZIONE ---
    # sample_player è un dizionario, estrai l'ID del player
    player_obj = sample_player["player"]
    # --- FINE CORREZIONE ---

    tp = TournamentPlayer(
        tournament_id=sample_tournament.id,
        player_id=player_obj.id,  # Usa l'ID dell'oggetto
        rebuy=1,
        rebuy_total_spent=sample_tournament.buy_in,
        prize=Decimal("100.00"),
        posizione=1,
    )
    db_session.add(tp)
    db_session.commit()

    # Ricarica per assicurare che le relazioni (come tp.tournament) siano caricate
    db_session.refresh(tp)
    return tp


def test_total_spent_calculation(sample_tournament_player):
    """
    Testa il calcolo di 'total_spent'.
    (Coverage stats.py: righe 34-37)
    """
    tp = sample_tournament_player

    # buy_in (100) + rebuy_total_spent (100) = 200
    expected_spent = tp.tournament.buy_in + tp.rebuy_total_spent
    assert tp.total_spent == expected_spent.quantize(Decimal("0.01"))
    assert tp.total_spent == Decimal("200.00")


def test_tournament_profit_positive(sample_tournament_player):
    """
    Testa il calcolo di 'tournament_profit' con un premio.
    (Coverage stats.py: righe 50-53)
    """
    tp = sample_tournament_player

    # prize (100) - total_spent (200) = -100
    expected_profit = tp.prize - tp.total_spent
    assert tp.tournament_profit == expected_profit.quantize(Decimal("0.01"))
    assert tp.tournament_profit == Decimal("-100.00")


def test_tournament_profit_zero_if_no_prize(
    db_session, sample_player, sample_tournament
):
    """
    Testa il profitto quando 'prize' è None.
    (Coverage stats.py: riga 50)
    """
    add_stats_properties(TournamentPlayer)

    # --- CORREZIONE ---
    player_obj = sample_player["player"]
    # --- FINE CORREZIONE ---

    tp = TournamentPlayer(
        tournament_id=sample_tournament.id,
        player_id=player_obj.id,
        rebuy=0,
        rebuy_total_spent=Decimal("0.00"),
        prize=None,  # Nessun premio
        posizione=2,
    )
    db_session.add(tp)
    db_session.commit()
    db_session.refresh(tp)  # Carica la relazione

    # prize (0.00) - total_spent (100.00) = -100.00
    assert tp.total_spent == sample_tournament.buy_in.quantize(Decimal("0.01"))
    assert tp.tournament_profit == Decimal("-100.00")


def test_stats_with_detached_tournament(sample_player):
    """
    Testa il "sad path" in cui la relazione .tournament non è caricata.
    (Coverage stats.py: riga 32)
    """
    add_stats_properties(TournamentPlayer)
    player_obj = sample_player["player"]

    # Crea un'istanza "orfana" senza un torneo
    tp = TournamentPlayer(
        player_id=player_obj.id, rebuy=1, rebuy_total_spent=Decimal("50.00")
    )

    # tp.tournament è None, quindi total_spent deve essere 0
    assert tp.tournament is None
    assert tp.total_spent == Decimal("0.00")

    # Di conseguenza, il profitto è solo il premio (se c'è)
    tp.prize = Decimal("100.00")
    assert tp.tournament_profit == Decimal("100.00")
