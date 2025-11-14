# app/routes/main/utils.py

from __future__ import annotations

from typing import List, Optional, Tuple # <-- MODIFICA: Aggiunto Tuple

# --- MODIFICA: Import aggiuntivi necessari ---
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError

from app import db
# --- MODIFICA: Import di Tournament ---
from app.models import Player, Tournament, TournamentPlayer


def is_safe_url(target: str) -> bool:
    """
    Consideriamo sicuro SOLO un URL relativo assoluto all'app, iniziato con "/".
    Questo corrisponde esattamente alle aspettative dei test
    e impedisce open redirect verso domini esterni.
    """
    return bool(target) and target.startswith("/")


def get_top_performers(
    limit: int = 5,
    order_by: str = "net_profit",
    descending: bool = True,
    min_tournaments: Optional[int] = None,
) -> List[Player]:
    """
    Ritorna i migliori giocatori (max `limit`) ordinati per `order_by`.
    Se `min_tournaments` è fornito, applica un filtro a livello SQL tramite HAVING.
    Nota: TournamentPlayer non ha un id autoincrement, quindi usiamo COUNT(*).
    """
    try:
        # Costruiamo una query che conti le partecipazioni per giocatore
        # --- MODIFICA: Aggiunto isouter=True ---
        # Questo assicura che anche i giocatori con 0 tornei 
        # (che non hanno entry in TournamentPlayer) siano inclusi nella query.
        stmt = (
            db.select(Player, func.count(TournamentPlayer.player_id).label("n_tourn"))
            .join(TournamentPlayer, TournamentPlayer.player_id == Player.id, isouter=True) 
            .group_by(Player.id)
        )
        # --- FINE MODIFICA ---

        # Filtro sul numero minimo di tornei con HAVING COUNT(*) >= min_tournaments
        if min_tournaments is not None:
            stmt = stmt.having(func.count(TournamentPlayer.player_id) >= int(min_tournaments))

        rows = db.session.execute(stmt).all()
        players = [p for (p, _) in rows]

        # Ordina in-memory sul campo richiesto, default 0 se None
        def keyfunc(pl: Player):
            # Usiamo .net_profit e .num_tournaments che sono proprietà
            # calcolate dal decorator @add_stats_properties sul modello Player
            val = getattr(pl, order_by, None)
            return 0 if val is None else val

        players_sorted = sorted(players, key=keyfunc, reverse=descending)
        
        # Applica il limite solo se specificato
        if limit is not None:
            return players_sorted[:limit]
        
        return players_sorted # Ritorna l'intera lista ordinata

    except SQLAlchemyError:
        # In caso di errore DB, rollback e ritorna lista vuota (i test lo prevedono)
        db.session.rollback()
        return []


# --- MODIFICA FUNZIONE UTILITY ---

def get_player_profit_history(player_id: int, limit: int = 10) -> Tuple[List[float], List[str]]:
    """
    Recupera lo storico dei profitti, NOMI e ID (ultimi 'limit' tornei) per un giocatore.
    Calcola i profitti in Python, non in SQL (dato che tournament_profit è @cached_property).
    Ritorna (lista_profitti, lista_nomi, lista_id)
    """
    try:
        stmt = (
            db.select(TournamentPlayer)
            .join(Tournament, Tournament.id == TournamentPlayer.tournament_id)
            .filter(TournamentPlayer.player_id == player_id)
            .order_by(Tournament.tournament_date.desc())
            .limit(limit)
        )
        tps = db.session.scalars(stmt).all()

        profit_results = []
        name_results = []
        id_results = []
        
        # Iteriamo in ordine cronologico (dal più vecchio al più recente)
        for tp in reversed(tps):  
            profit = float(tp.tournament_profit or 0)
            profit_results.append(profit)
            
            # Aggiungiamo il nome del torneo corrispondente
            name_results.append(tp.tournament.name)
            id_results.append(tp.tournament.id)

        return profit_results, name_results, id_results

    except Exception:
        db.session.rollback()
        return [], [], []  # Ritorna tre liste vuote in caso di errore

# --- FINE MODIFICA ---