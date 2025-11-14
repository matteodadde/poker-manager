# app/routes/players/utils.py
"""
Funzioni di utilità per le route dei giocatori.
"""
from typing import List, Optional, Dict, Any
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func  # <-- Aggiunto func per l'ottimizzazione
from decimal import Decimal
# Importa i modelli e db
from app import db
from app.models import Player, TournamentPlayer

# Importa helper per arrotondamento e emoji
from app.utils.decimal import round_decimal

# Rinomina per evitare conflitto con 'Player'
from app.models.player.validators import validate_country as validate_country_code


def country_code_to_emoji(code: Optional[str]) -> str:
    """Converte un codice paese ISO a 2 lettere nella sua emoji bandiera."""
    if not code:
        return ""
    # Valida il codice prima di convertirlo
    try:
        valid_code = validate_country_code(code)
        if not valid_code:
            return ""
        OFFSET = 127397
        return "".join(chr(ord(c) + OFFSET) for c in valid_code.upper())
    except ValueError:
        return ""  # Restituisce stringa vuota se il codice non è valido


def get_player_stats(player: Player) -> Dict[str, Any]:
    """
    Restituisce un dizionario con le statistiche del giocatore,
    già formattate per la visualizzazione.
    """
    stats = {
        # Usa round_decimal per formattare i valori Decimal
        "total_winnings": round_decimal(player.total_winnings),
        "total_buyin_spent": round_decimal(player.total_buyin_spent),
        "total_rebuy_spent": round_decimal(player.total_rebuy_spent),
        "total_spent": round_decimal(player.total_spent),
        "net_profit": round_decimal(player.net_profit),
        "roi": round_decimal(player.roi) if player.roi is not None else Decimal("0.00"),
        # Interi e float possono rimanere così
        "num_tournaments": player.num_tournaments or 0,
        "num_wins": player.num_wins or 0,
        "win_rate": round(player.win_rate, 2) if player.win_rate is not None else 0.0,
        "in_the_money": player.in_the_money or 0,
        "itm_rate": round(player.itm_rate, 2) if player.itm_rate is not None else 0.0,
        "num_rebuy": player.num_rebuy or 0,
        "avg_profit_per_tournament": round_decimal(player.avg_profit_per_tournament),
        "avg_rebuy_per_tournament": round(player.avg_rebuy_per_tournament, 2)
        if player.avg_rebuy_per_tournament is not None
        else 0.0,
        "avg_prize_when_paid": round_decimal(player.avg_prize_when_paid),
        "win_to_itm_ratio": round(player.win_to_itm_ratio, 2)
        if player.win_to_itm_ratio is not None
        else 0.0,
        "num_zero_rebuy_tournaments": player.num_zero_rebuy_tournaments or 0,
        "abi": round_decimal(player.abi),
        "cpc": round_decimal(player.cpc),
        "rebuy_tournaments": player.rebuy_tournaments or 0,
        "rebuy_frequency": round_decimal(player.rebuy_frequency) if player.rebuy_frequency is not None else Decimal("0.00"),
        # Aggiungi l'emoji del paese
        "country_emoji": country_code_to_emoji(player.country),
    }
    return stats


def get_top_performers(
    limit: int = 5,
    order_by: str = "net_profit",
    descending: bool = True,
    min_tournaments: Optional[int] = None,
) -> List[Player]:
    """
    Recupera i migliori giocatori ordinati per un campo specificato.
    Usa le @cached_property dei modelli Player per l'ordinamento in Python,
    ma filtra per 'min_tournaments' nel DB per efficienza.
    """
    try:
        current_app.logger.debug(
            f"Recupero top {limit} giocatori per {order_by} ({'desc' if descending else 'asc'})"
        )

        # Sintassi SQLAlchemy 2.0:
        # Seleziona tutti i giocatori
        stmt = db.select(Player)

        # --- OTTIMIZZAZIONE ---
        # Se è richiesto un numero minimo di tornei,
        # filtriamo nel DB usando un JOIN e un GROUP BY / HAVING
        # prima di caricare gli oggetti in memoria.
        if min_tournaments is not None and min_tournaments > 0:
            # --- CORREZIONE DEL BUG ---
            # Sostituisci TournamentPlayer.id (che non esiste)
            # con TournamentPlayer.player_id (che esiste)
            stmt = (
                stmt.join(TournamentPlayer, TournamentPlayer.player_id == Player.id)
                .group_by(Player.id)
                .having(
                    func.count(TournamentPlayer.player_id) >= min_tournaments
                )  # <-- CORRETTO
            )
            # --- FINE CORREZIONE ---

        else:
            # Se non filtriamo, assicuriamoci comunque di prendere solo
            # giocatori che hanno ALMENO una partecipazione (come da logica originale)
            stmt = stmt.join(
                TournamentPlayer, TournamentPlayer.player_id == Player.id
            ).distinct()
        # --- FINE OTTIMIZZAZIONE ---

        players = list(
            db.session.scalars(stmt).all()
        )  # Esegui la query (ora pre-filtrata)

        # Filtro per minimo tornei (NON PIÙ NECESSARIO, già fatto in DB)
        # if min_tournaments is not None:
        #     players = [
        #         p for p in players if (p.num_tournaments or 0) >= min_tournaments
        #     ]

        # Filtra solo quelli con attributo valido (in Python, per le @cached_property)
        filtered_players = [
            p
            for p in players
            if hasattr(p, order_by) and getattr(p, order_by) is not None
        ]

        # Ordina (in Python, usando la cached_property)
        sorted_players = sorted(
            filtered_players, key=lambda p: getattr(p, order_by), reverse=descending
        )

        top_players = sorted_players[:limit]

        current_app.logger.debug(f"Trovati {len(top_players)} top performers")
        return top_players

    except SQLAlchemyError as e:
        current_app.logger.error(
            f"Errore DB durante il recupero dei top performers: {e}", exc_info=True
        )
        db.session.rollback()
        return []
    except Exception as e:
        # Cattura altri errori potenziali (es. AttributeError se order_by non esiste)
        current_app.logger.error(
            f"Errore imprevisto durante il recupero dei top performers: {e}",
            exc_info=True,
        )
        return []
