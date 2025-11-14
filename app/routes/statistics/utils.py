from sqlalchemy import func, desc, case, Numeric, cast
from app.models import Player, TournamentPlayer, Tournament
from types import SimpleNamespace
from decimal import Decimal
from app import db


def get_leaderboard_stats():
    # === Espressioni SQL ===
    total_winnings_expr = func.coalesce(
        func.sum(func.coalesce(TournamentPlayer.prize, 0)), 0
    )
    rebuy_spent_expr = func.coalesce(
        func.sum(func.coalesce(TournamentPlayer.rebuy_total_spent, 0)), 0
    )
    buyin_spent_expr = func.coalesce(func.sum(func.coalesce(Tournament.buy_in, 0)), 0)
    num_rebuy_expr = func.coalesce(
        func.sum(func.coalesce(TournamentPlayer.rebuy, 0)), 0
    )
    num_tournaments_expr = func.count(TournamentPlayer.tournament_id)
    num_wins_expr = func.coalesce(
        func.sum(case((TournamentPlayer.posizione == 1, 1), else_=0)), 0
    )
    itm_expr = func.coalesce(
        func.sum(case((TournamentPlayer.prize > 0, 1), else_=0)), 0
    )
    num_zero_rebuy_tournaments_expr = func.coalesce(
        func.sum(case((TournamentPlayer.rebuy == 0, 1), else_=0)), 0
    )

    # === Query ===
    results = (
        db.session.query(
            Player,
            total_winnings_expr.label("total_winnings"),
            rebuy_spent_expr.label("total_rebuy_spent"),
            buyin_spent_expr.label("total_buyin_spent"),
            num_rebuy_expr.label("num_rebuy"),
            num_tournaments_expr.label("num_tournaments"),
            num_wins_expr.label("num_wins"),
            itm_expr.label("in_the_money"),
            num_zero_rebuy_tournaments_expr.label("num_zero_rebuy_tournaments"),
        )
        .select_from(Player)
        .outerjoin(TournamentPlayer, TournamentPlayer.player_id == Player.id)
        .outerjoin(Tournament, Tournament.id == TournamentPlayer.tournament_id)
        .group_by(Player.id)
        .all()
    )

    # === Costruzione Lista Risultati ===
    leaderboard = []
    for (
        player,
        total_winnings,
        total_rebuy_spent,
        total_buyin_spent,
        num_rebuy,
        num_tournaments,
        num_wins,
        in_the_money,
        num_zero_rebuy_tournaments,
    ) in results:
        # Conversione e Coalesce
        total_winnings = Decimal(total_winnings or 0)
        total_rebuy_spent = Decimal(total_rebuy_spent or 0)
        total_buyin_spent = Decimal(total_buyin_spent or 0)
        num_rebuy = int(num_rebuy or 0)
        num_tournaments = int(num_tournaments or 0)
        num_wins = int(num_wins or 0)
        in_the_money = int(in_the_money or 0)
        num_zero_rebuy_tournaments = int(num_zero_rebuy_tournaments or 0)

        # Calcoli Base
        total_spent = total_buyin_spent + total_rebuy_spent
        net_profit = total_winnings - total_spent

        # Calcoli Derivati esistenti
        win_rate = (num_wins / num_tournaments) if num_tournaments else 0.0
        itm_rate = (in_the_money / num_tournaments) if num_tournaments else 0.0
        avg_profit_per_tournament = (
            (net_profit / num_tournaments) if num_tournaments else Decimal("0.00")
        )
        avg_rebuy_per_tournament = (
            (Decimal(num_rebuy) / num_tournaments)
            if num_tournaments
            else Decimal("0.00")
        )
        avg_prize_when_paid = (
            (total_winnings / in_the_money) if in_the_money else Decimal("0.00")
        )
        win_to_itm_ratio = (num_wins / in_the_money) if in_the_money else 0.0
    
        abi = (
            (total_buyin_spent / num_tournaments)
            if num_tournaments
            else Decimal("0.00")
        )
        
        cpc = (
            (total_spent / in_the_money) 
            if in_the_money 
            else Decimal("0.00")
        )
        
        roi = (
            (net_profit / total_spent * 100)
            if total_spent > 0
            else Decimal("0.00")
        )
        rebuy_tournaments = Decimal(num_tournaments) - Decimal(num_zero_rebuy_tournaments)

        rebuy_frequency = (
            (rebuy_tournaments / Decimal(num_tournaments)) * Decimal("100")
            if num_tournaments > 0
            else Decimal("0.00")
        )


        leaderboard.append(
            SimpleNamespace(
                player_id=player.id,
                nickname=player.nickname,
                avatar_url=player.avatar_url,
                net_profit=net_profit,
                roi=roi,
                num_tournaments=num_tournaments,
                num_wins=num_wins,
                in_the_money=in_the_money,
                total_winnings=total_winnings,
                total_rebuy_spent=total_rebuy_spent,
                total_buyin_spent=total_buyin_spent,
                total_spent=total_spent,
                num_rebuy=num_rebuy,
                win_rate=win_rate,
                itm_rate=itm_rate,
                avg_profit_per_tournament=avg_profit_per_tournament,
                avg_rebuy_per_tournament=avg_rebuy_per_tournament,
                avg_prize_when_paid=avg_prize_when_paid,
                win_to_itm_ratio=win_to_itm_ratio,
                num_zero_rebuy_tournaments=num_zero_rebuy_tournaments,
                abi=abi,
                cpc=cpc,
                rebuy_tournaments=rebuy_tournaments,
                rebuy_frequency=rebuy_frequency,
            )
        )

    # Filtra i giocatori che non hanno mai giocato
    leaderboard = [row for row in leaderboard if row.num_tournaments > 0]
    return leaderboard