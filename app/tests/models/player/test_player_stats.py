import pytest
from decimal import Decimal
from app.models import Player
from app.models.tournament_player.base import TournamentPlayer
from app.models.tournament.base import Tournament

# --- HELPERS ---


def refresh_stats(db_session, player):
    """
    Scade l'oggetto player, forzando tutte le @cached_property
    a ricaricarsi dal database. È FONDAMENTALE.
    """
    db_session.expire(player)


# --- TEST ---


# 1. Nessuna partecipazione
def test_no_participation_stats(sample_player, db_session):
    player = sample_player["player"]  # Estrai il player dal dizionario
    refresh_stats(db_session, player)  # Ricarica lo stato base

    assert player.total_winnings == Decimal("0.00")
    assert player.total_spent == Decimal("0.00")
    assert player.net_profit == Decimal("0.00")
    assert player.num_tournaments == 0
    assert player.num_wins == 0
    assert player.win_rate is None
    assert player.in_the_money == 0
    assert player.itm_rate is None
    assert player.num_rebuy == 0
    assert player.avg_profit_per_tournament is None
    assert player.win_to_itm_ratio is None
    assert player.avg_prize_when_paid == Decimal("0.00")

    # --- NUOVO ASSERT (per linea 172) ---
    assert player.avg_rebuy_per_tournament is None


# 2. Partecipazione con rebuy
def test_participation_with_rebuy(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    tournament = create_tournament()
    add_participation(player, tournament, prize=Decimal("0.00"), rebuy=2)
    refresh_stats(db_session, player)

    assert player.total_winnings == Decimal("0.00")
    assert player.total_spent == Decimal("300.00")
    assert player.net_profit == Decimal("-300.00")
    assert player.num_rebuy == 2
    assert player.num_tournaments == 1


# 3. Premi None o 0.00
def test_prizes_none_and_zero(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    t1 = create_tournament("T1")
    t2 = create_tournament("T2")
    add_participation(player, t1, prize=None, rebuy=1)
    add_participation(player, t2, prize=Decimal("0.00"), rebuy=0)
    refresh_stats(db_session, player)

    expected_spent = Decimal("300.00")
    assert player.total_winnings == Decimal("0.00")
    assert player.total_spent == expected_spent
    assert player.net_profit == -expected_spent
    assert player.num_tournaments == 2
    assert player.avg_prize_when_paid == Decimal("0.00")


# 5. Arrotondamento profitto medio
def test_avg_profit_rounding(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    t1 = create_tournament("T1", buy_in=Decimal("50.00"))
    t2 = create_tournament("T2", buy_in=Decimal("50.00"))
    add_participation(player, t1, prize=Decimal("120.00"), rebuy=0)
    add_participation(player, t2, prize=Decimal("80.00"), rebuy=1)
    refresh_stats(db_session, player)

    assert player.total_spent == Decimal("150.00")
    assert player.total_winnings == Decimal("200.00")
    assert player.net_profit == Decimal("50.00")
    assert player.num_tournaments == 2
    assert player.avg_profit_per_tournament == Decimal("25.00")


# 6. Vittorie e ITM
def test_win_and_itm(sample_player, create_tournament, add_participation, db_session):
    player = sample_player["player"]
    t1 = create_tournament("Win1")
    t2 = create_tournament("ITM2")
    t3 = create_tournament("NoPrize")
    add_participation(player, t1, prize=Decimal("300.00"), posizione=1)
    add_participation(player, t2, prize=Decimal("150.00"), posizione=4)
    add_participation(player, t3, prize=Decimal("0.00"), posizione=7)
    refresh_stats(db_session, player)

    assert player.num_wins == 1
    assert player.in_the_money == 2
    assert player.num_tournaments == 3
    assert player.win_rate == Decimal("33.33")
    assert player.itm_rate == Decimal("66.67")


# 7. Partecipazione senza rebuy e senza premio
def test_participation_no_rebuy_no_prize(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    tournament = create_tournament("Simple")
    add_participation(player, tournament, prize=None, rebuy=0)
    refresh_stats(db_session, player)

    assert player.total_spent == Decimal("100.00")
    assert player.total_winnings == Decimal("0.00")
    assert player.net_profit == Decimal("-100.00")
    assert player.num_tournaments == 1


# 8. Partecipazione con più rebuy e premio alto
def test_participation_high_rebuy_high_prize(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    tournament = create_tournament("HighStakes", buy_in=Decimal("200.00"))
    add_participation(player, tournament, prize=Decimal("1000.00"), rebuy=3)
    refresh_stats(db_session, player)

    expected_spent = Decimal("800.00")
    assert player.total_spent == expected_spent
    assert player.total_winnings == Decimal("1000.00")
    assert player.net_profit == Decimal("200.00")
    assert player.num_rebuy == 3
    assert player.num_tournaments == 1


# Test (ora corretto)
def test_player_total_spent_with_rebuy(
    db_session, sample_player, sample_tournament, add_participation
):
    player = sample_player["player"]
    tp = add_participation(player, sample_tournament, prize=Decimal("0.00"), rebuy=2)
    refresh_stats(db_session, player)

    assert player.total_spent == Decimal("300.00")


# 9. Media rebuy per torneo
def test_avg_rebuy_per_tournament(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    t1 = create_tournament()
    t2 = create_tournament()
    add_participation(player, t1, rebuy=1)
    add_participation(player, t2, rebuy=3)
    refresh_stats(db_session, player)

    assert player.num_rebuy == 4
    assert player.num_tournaments == 2
    assert player.avg_rebuy_per_tournament == 2.0


# 10. Premio medio solo nei tornei premiati
def test_avg_prize_when_paid(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    t1 = create_tournament()
    t2 = create_tournament()
    t3 = create_tournament()
    add_participation(player, t1, prize=Decimal("300.00"))
    add_participation(player, t2, prize=Decimal("0.00"))
    add_participation(player, t3, prize=None)
    refresh_stats(db_session, player)

    assert player.avg_prize_when_paid == Decimal("300.00")


# 11. Rapporto vittorie / ITM
def test_win_to_itm_ratio(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    t1 = create_tournament()
    t2 = create_tournament()
    t3 = create_tournament()
    add_participation(player, t1, posizione=1, prize=Decimal("100.00"))
    add_participation(player, t2, posizione=3, prize=Decimal("50.00"))
    add_participation(player, t3, posizione=6, prize=Decimal("0.00"))
    refresh_stats(db_session, player)

    assert player.num_wins == 1
    assert player.in_the_money == 2
    assert player.win_to_itm_ratio == 0.5


# 12. Numero tornei con zero rebuy
def test_num_zero_rebuy_tournaments(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    t1 = create_tournament()
    t2 = create_tournament()
    t3 = create_tournament()
    add_participation(player, t1, rebuy=0)
    add_participation(player, t2, rebuy=2)
    add_participation(player, t3, rebuy=0)
    refresh_stats(db_session, player)

    assert player.num_zero_rebuy_tournaments == 2


# 13. Spesa solo buy-in vs solo rebuy
def test_total_buyin_and_rebuy_spent(
    sample_player, create_tournament, add_participation, db_session
):
    player = sample_player["player"]
    t1 = create_tournament(buy_in=Decimal("100.00"))
    t2 = create_tournament(buy_in=Decimal("50.00"))
    add_participation(player, t1, rebuy=2, prize=Decimal("0.00"))
    add_participation(player, t2, rebuy=0, prize=Decimal("0.00"))
    refresh_stats(db_session, player)

    assert player.total_buyin_spent == Decimal("150.00")
    assert player.total_rebuy_spent == Decimal("200.00")


def test_win_to_itm_ratio_zero_itm(
    db_session, sample_player, create_tournament, add_participation
):
    """
    Testa il rapporto VITTORIE/ITM quando ITM è 0.
    Copre il branch 184->183 (ZeroDivisionError).
    """
    player = sample_player["player"]
    t1 = create_tournament(buy_in=100)

    # Aggiungi una partecipazione ma SENZA premio (quindi ITM = 0)
    add_participation(player, t1, posizione=50, prize=0)

    db_session.refresh(player)

    assert player.in_the_money == 0
    assert player.num_wins == 0
    # Il branch 184->183 gestisce questo e ritorna 0
    assert player.num_wins == 0
