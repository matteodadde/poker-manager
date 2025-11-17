# app/tests/performance/test_performance_queries.py

import pytest
from decimal import Decimal
from datetime import date


@pytest.mark.benchmark(group="players")
def test_get_top_performers_performance(
    db_session, multiple_players, add_participation, benchmark
):
    """
    Verifica che la query che calcola i top performer rimanga efficiente
    anche con molti giocatori e partecipazioni.
    """
    # Arrange: molti giocatori
    players = multiple_players(200)

    # Aggiungi partecipazioni realistiche
    from app.models import Tournament

    t = Tournament(
        name="PerfTest",
        buy_in=Decimal("50.00"),
        tournament_date=date.today(),
        admin_id=players[0].id,
    )
    db_session.add(t)
    db_session.commit()

    for p in players:
        add_participation(player=p, tournament=t, prize=Decimal("0"), rebuy=1)

    from app.routes.players.utils import get_top_performers

    # Benchmark: misura solo la query core
    result = benchmark(lambda: get_top_performers(limit=20))

    # Assert: risultato plausibile
    assert len(result) <= 20


@pytest.mark.benchmark(group="statistics")
def test_leaderboard_performance(
    db_session, multiple_players, add_participation, benchmark
):
    """
    Testa la performance del leaderboard globale.
    """
    players = multiple_players(150)

    from app.models import Tournament

    t = Tournament(
        name="LeaderboardPerf",
        buy_in=Decimal("80.00"),
        tournament_date=date.today(),
        admin_id=players[0].id,
    )
    db_session.add(t)
    db_session.commit()

    for p in players:
        add_participation(player=p, tournament=t, prize=Decimal("0"), rebuy=2)

    from app.routes.statistics.utils import get_leaderboard_stats

    result = benchmark(lambda: get_leaderboard_stats())

    assert isinstance(result, list)


@pytest.mark.benchmark(group="tournaments")
def test_tournament_stats_performance(
    db_session, sample_player, add_participation, benchmark
):
    """
    Verifica la performance del calcolo statistiche torneo con molti partecipanti.
    """
    from app.models import Tournament

    t = Tournament(
        name="StatsPerf",
        buy_in=Decimal("50.00"),
        prize_pool=Decimal("2000.00"),
        tournament_date=date.today(),
        admin_id=sample_player["player"].id,
    )
    db_session.add(t)
    db_session.commit()

    # 120 partecipanti simulati
    from app.models import Player

    players = []
    for i in range(120):
        p = Player(
            first_name="X",
            last_name="Y",
            nickname=f"pp{i}",
            email=f"mail{i}@x.com",
            password_hash="hash",
        )
        db_session.add(p)
        players.append(p)
    db_session.commit()

    for p in players:
        add_participation(player=p, tournament=t, prize=None, rebuy=1)

    from app.models.tournament.stats import effective_prize_pool, ordered_players

    # Misuriamo funzioni aggregate reali
    benchmark(lambda: (effective_prize_pool(t), ordered_players(t)))
