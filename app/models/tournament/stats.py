# app/models/tournament/stats.py

"""
Modulo Statistiche Torneo (Business Logic).

Questo modulo definisce funzioni pure o context-bound per il calcolo delle metriche
finanziarie e di classifica di un torneo.

ARCHITETTURA & PERFORMANCE:
Le funzioni qui definite operano in modalità "In-Memory".
Non eseguono query SQL aggiuntive, ma iterano sulle collezioni (liste) già caricate
nell'oggetto `Tournament`.

ATTENZIONE (N+1 PROBLEM):
Affinché queste proprietà siano performanti, la rotta o il controller che carica il Torneo
DEVE pre-caricare la relazione `tournament_players` (Eager Loading).
In SQLAlchemy: `query.options(selectinload(Tournament.tournament_players))`
Se ciò non avviene, accedere a queste proprietà scatenerà una query SQL per ogni torneo (Lazy Loading),
degradando le prestazioni.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List
from decimal import Decimal
from werkzeug.utils import cached_property  # Import essenziale per la memoizzazione

from app.utils.decimal import round_decimal

# Le dipendenze qui sono solo per il Type Hinting statico.
# A runtime, questo modulo lavora sugli oggetti passati come 'self'.
if TYPE_CHECKING:
    from app.models.tournament.base import Tournament
    from app.models.tournament_player.base import TournamentPlayer


def effective_prize_pool(self: Tournament) -> Decimal:
    """
    Calcola il Montepremi (Prize Pool) Definitivo.

    Logica di Business:
    1. OVERRIDE MANUALE: Se l'admin ha impostato un `prize_pool` fisso (es. Garantito),
       questo vince su qualsiasi calcolo matematico.
    2. CALCOLO DINAMICO: Se non c'è un fisso, il montepremi è la somma di:
       (Buy-in * Numero Giocatori) + (Totale speso in Rebuy/Add-on).

    Returns:
        Decimal: Il totale monetario arrotondato.
    """
    # Controllo priorità: Il valore esplicito nel DB ha la precedenza.
    if self.prize_pool is not None and self.prize_pool > 0:
        return round_decimal(self.prize_pool)

    # Calcolo Base: Buy-in x Iscritti.
    # Nota: self.num_players è una @cached_property nel modello base, quindi efficiente.
    base = self.buy_in * self.num_players

    # Calcolo Extra: Iterazione in memoria per sommare i rebuy.
    # Performance: Qui assumiamo che 'tournament_players' sia già in RAM (Eager Loaded).
    total_rebuy_spent = sum(
        tp.rebuy_total_spent or Decimal("0.00") for tp in self.tournament_players
    )

    total = base + total_rebuy_spent
    return round_decimal(total)


def ordered_players(self: Tournament) -> List[TournamentPlayer]:
    """
    Genera la Leaderboard del torneo.

    Ordina la lista dei partecipanti basandosi sul campo 'posizione'.
    Gestisce casi misti (giocatori eliminati vs giocatori ancora in gioco/senza posizione).

    Returns:
        List[TournamentPlayer]: La lista ordinata (1°, 2°, 3°... seguito dai non classificati).
    """
    all_players = self.tournament_players

    # Divide et Impera: Separiamo chi ha una posizione ufficiale da chi non l'ha ancora.
    defined_position = [tp for tp in all_players if tp.posizione is not None]
    undefined_position = [tp for tp in all_players if tp.posizione is None]

    # Ordinamento stabile sui classificati + accodamento dei non classificati.
    sorted_players = (
        sorted(defined_position, key=lambda p: p.posizione) + undefined_position
    )

    return sorted_players


def num_rebuys(self: Tournament) -> int:
    """
    Metrica di Volume: Totale Rebuy.
    Somma il contatore 'rebuy' di ogni singolo giocatore.
    """
    return sum(tp.rebuy or 0 for tp in self.tournament_players)


def total_rebuy_spent(self: Tournament) -> Decimal:
    """
    Metrica Finanziaria: Totale incassato dai Rebuy.
    Somma il valore monetario dei rebuy di tutti i giocatori.
    """
    total = sum(
        tp.rebuy_total_spent or Decimal("0.00") for tp in self.tournament_players
    )
    return round_decimal(total)


# -------------------------
# Pattern: Decorator Injection
# -------------------------


def add_stats_properties(cls: type[Tournament]) -> type[Tournament]:
    """
    Decoratore per arricchire la classe Tournament.

    Inietta le funzioni di calcolo come `cached_property`.
    
    Perché cached_property?
    Questi calcoli, seppur in memoria, richiedono iterazioni su liste potenzialmente lunghe.
    Memoizzando il risultato sull'istanza (`self`), garantiamo che il calcolo avvenga
    una sola volta per Request/Ciclo di vita dell'oggetto, anche se la proprietà
    viene acceduta 50 volte in un template HTML.

    Args:
        cls: La classe Tournament da decorare.

    Returns:
        La classe Tournament arricchita.
    """
    cls.total_prize_pool = cached_property(effective_prize_pool)
    cls.ordered_players = cached_property(ordered_players)
    cls.num_rebuys = cached_property(num_rebuys)
    cls.total_rebuy_spent = cached_property(total_rebuy_spent)
    return cls