import pytest
from decimal import Decimal
from app.models import Tournament, Player, TournamentPlayer
from app import db


def clear_cache(tournament):
    """
    Helper per invalidare manualmente TUTTE le cached_property
    definite in stats.py.
    """
    props_to_clear = [
        "total_prize_pool",
        "ordered_players",
        "num_rebuys",
        "total_rebuy_spent",
    ]
    for prop in props_to_clear:
        # Usa hasattr per controllare prima di cancellare
        if hasattr(tournament, prop):
            try:
                delattr(tournament, prop)
            except AttributeError:
                pass  # Va bene, la cache non era popolata


def test_prize_pool_explicit(
    db_session, create_tournament, add_participation, sample_player
):
    """
    Testa Path 1: total_prize_pool usa il valore esplicito se fornito.
    (Coverage righe 38-39)
    """
    admin = sample_player["player"]

    tournament = create_tournament(
        name="Torneo Garantito",
        prize_pool=Decimal("1000.00"),  # Valore esplicito
        buy_in=Decimal("50.00"),
    )

    # Passa rebuy=1, ma la fixture calcolerà 1*50=50 per rebuy_total_spent
    add_participation(admin, tournament, rebuy=1)

    clear_cache(tournament)

    # Il montepremi deve essere quello esplicito, non quello calcolato
    assert tournament.total_prize_pool == Decimal("1000.00")


def test_prize_pool_calculated(
    db_session, create_tournament, add_participation, multiple_players
):
    """
    Testa Path 2: total_prize_pool calcola (buy_in * players) + rebuy_spent.
    (Coverage righe 43-51)
    """
    tournament = create_tournament(buy_in=Decimal("100.00"), prize_pool=None)
    players = multiple_players(3)

    # La fixture calcola i totali:
    add_participation(players[0], tournament, rebuy=1)  # rebuy_total = 100
    add_participation(players[1], tournament, rebuy=2)  # rebuy_total = 200
    add_participation(players[2], tournament, rebuy=0)  # rebuy_total = 0

    clear_cache(tournament)

    # Calcolo atteso:
    # 3 Giocatori -> num_players = 3 (da base.py)
    # Base = 3 * 100.00 (buy_in) = 300.00
    # Rebuys = 100.00 + 200.00 + 0.00 = 300.00
    # Totale = 300.00 + 300.00 = 600.00
    assert tournament.num_players == 3
    assert tournament.total_rebuy_spent == Decimal("300.00")
    assert tournament.total_prize_pool == Decimal("600.00")


def test_prize_pool_calculated_half_rebuy(
    db_session, create_tournament, add_participation, multiple_players
):
    """
    Testa il calcolo con rebuy_total_spent diverso (metà prezzo).
    """
    tournament = create_tournament(buy_in=Decimal("100.00"), prize_pool=None)
    players = multiple_players(2)

    # Usa l'override della fixture
    add_participation(
        players[0], tournament, rebuy=1, rebuy_total_spent=Decimal("50.00")
    )  # Metà prezzo
    add_participation(
        players[1], tournament, rebuy=0, rebuy_total_spent=Decimal("0.00")
    )

    clear_cache(tournament)

    # Calcolo atteso:
    # 2 Giocatori -> num_players = 2
    # Base = 2 * 100.00 = 200.00
    # Rebuys = 50.00 + 0.00 = 50.00
    # Totale = 200.00 + 50.00 = 250.00
    assert tournament.num_players == 2
    assert tournament.total_rebuy_spent == Decimal("50.00")
    assert tournament.total_prize_pool == Decimal("250.00")


def test_prize_pool_calculated_with_nones(
    db_session, create_tournament, add_participation, multiple_players
):
    """
    Testa che il calcolo gestisca i 'None' nelle colonne (creati manualmente).
    """
    tournament = create_tournament(buy_in=Decimal("50.00"), prize_pool=None)
    players = multiple_players(2)

    add_participation(
        players[0], tournament, rebuy=1, rebuy_total_spent=Decimal("50.00")
    )

    # Aggiungi partecipazione manuale con None (i validatori lo permettono)
    tp = TournamentPlayer(
        player_id=players[1].id,
        tournament_id=tournament.id,
        rebuy=None,  # Valido (default=0)
        rebuy_total_spent=None,  # Valido (default=None)
    )
    db_session.add(tp)
    # Aggiungi manualmente alla lista in memoria
    tournament.tournament_players.append(tp)
    db_session.commit()

    clear_cache(tournament)

    # Calcolo atteso:
    # 2 Giocatori -> num_players = 2
    # Base = 2 * 50.00 = 100.00
    # Rebuys = 50.00 (player 0) + 0.00 (player 1, da None) = 50.00
    # Totale = 100.00 + 50.00 = 150.00
    assert tournament.num_players == 2
    assert tournament.total_rebuy_spent == Decimal("50.00")
    assert tournament.total_prize_pool == Decimal("150.00")


def test_ordered_players(
    db_session, create_tournament, add_participation, multiple_players
):
    """
    Testa l'ordinamento dei giocatori per 'posizione', con i None alla fine.
    (Coverage righe 59-70)
    """
    tournament = create_tournament()
    players = multiple_players(4)

    add_participation(players[0], tournament, posizione=3)
    add_participation(players[1], tournament, posizione=1)
    add_participation(players[2], tournament, posizione=None)  # Senza posizione
    add_participation(players[3], tournament, posizione=2)

    clear_cache(tournament)

    ordered = tournament.ordered_players

    assert len(ordered) == 4
    ordered_ids = [p.player_id for p in ordered]
    assert ordered_ids == [players[1].id, players[3].id, players[0].id, players[2].id]
    ordered_pos = [p.posizione for p in ordered]
    assert ordered_pos == [1, 2, 3, None]


def test_num_rebuys_and_total_spent(
    db_session, create_tournament, add_participation, multiple_players
):
    """
    Testa 'num_rebuys' (basato su 'rebuy') e 'total_rebuy_spent'.
    (Coverage righe 76, 86-89)
    """
    tournament = create_tournament(buy_in=Decimal("50.00"))
    players = multiple_players(3)

    add_participation(
        players[0], tournament, rebuy=2, rebuy_total_spent=Decimal("100.00")
    )
    add_participation(
        players[1], tournament, rebuy=1, rebuy_total_spent=Decimal("25.00")
    )  # Metà prezzo

    tp = TournamentPlayer(
        player_id=players[2].id,
        tournament_id=tournament.id,
        rebuy=None,
        rebuy_total_spent=None,
    )
    db_session.add(tp)
    tournament.tournament_players.append(tp)
    db_session.commit()

    clear_cache(tournament)

    # num_rebuys somma la colonna 'rebuy' (2 + 1 + 0)
    assert tournament.num_rebuys == 3
    # total_rebuy_spent somma 'rebuy_total_spent' (100 + 25 + 0)
    assert tournament.total_rebuy_spent == Decimal("125.00")


def test_stats_on_empty_tournament(db_session, create_tournament):
    """
    Testa tutti gli stats su un torneo senza giocatori.
    (Coverage righe 44, 62, 78)
    """
    tournament = create_tournament(prize_pool=None)

    clear_cache(tournament)

    assert tournament.num_players == 0
    assert tournament.total_rebuy_spent == Decimal("0.00")
    assert tournament.num_rebuys == 0
    assert tournament.ordered_players == []
    # (Base = 100 * 0) + (Rebuy = 0) = 0
    assert tournament.total_prize_pool == Decimal("0.00")
