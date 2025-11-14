# app/models/tournament_player/stats.py
"""
Statistiche Partecipazione (Financial Logic).

Questo modulo calcola le metriche finanziarie puntuali per la singola iscrizione
di un giocatore a un torneo.

Design Pattern:
Le funzioni sono definite esternamente per non appesantire la classe `TournamentPlayer`
(che è un Association Object) con logica di calcolo. Vengono iniettate dinamicamente
tramite il decoratore `@add_stats_properties` usando la memoizzazione (`cached_property`).

Vantaggi:
- Separation of Concerns: Il modello definisce i dati, questo modulo definisce i calcoli.
- Performance: I calcoli vengono eseguiti solo se richiesti e cachati per la durata dell'istanza.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from werkzeug.utils import cached_property  # Import essenziale per la memoizzazione

from app.utils.decimal import round_decimal

# Import solo per type checking statico (evita cicli a runtime)
if TYPE_CHECKING:
    from app.models.tournament_player.base import TournamentPlayer


def total_spent(self: TournamentPlayer) -> Decimal:
    """
    Calcola l'investimento totale (Gross Cost) per questo torneo.
    
    Formula: Buy-in del Torneo + Spesa Totale Rebuy.

    Dipendenze:
    Richiede che la relazione `self.tournament` sia accessibile.
    ATTENZIONE: Se `tournament` non è pre-caricato (Eager Loading),
    l'accesso a questa proprietà scatenerà una query SQL extra (Lazy Load).

    Returns:
        Decimal: La somma totale spesa, formattata a 2 decimali.
    """
    # Fail-safe: Se il torneo non è caricato o manca il buy-in (es. dati corrotti),
    # ritorniamo 0.00 per evitare crash in fase di rendering template.
    if not self.tournament or self.tournament.buy_in is None:
        return Decimal("0.00")

    # Conversione esplicita per sicurezza aritmetica
    buy_in = Decimal(self.tournament.buy_in)
    
    # rebuy_total_spent è già un campo calcolato persistito nel DB (o default 0.00)
    rebuy_spent = self.rebuy_total_spent or Decimal("0.00")
    
    total = buy_in + rebuy_spent
    return round_decimal(total)


def tournament_profit(self: TournamentPlayer) -> Decimal:
    """
    Calcola il Net Profit (PnL) per questo torneo.
    
    Formula: Premio Vinto (Cashout) - Totale Speso.
    
    Nota:
    Il risultato può essere negativo (Loss) se il giocatore non è andato a premio
    o se il premio è inferiore alla spesa (es. min-cash con molti rebuy).

    Returns:
        Decimal: Profitto (o perdita) netto.
    """
    prize = self.prize or Decimal("0.00")

    # Sfrutta la proprietà cachata `self.total_spent` definita sopra.
    # Questo assicura che non ricalcoliamo il buy-in+rebuy ogni volta.
    return round_decimal(prize - self.total_spent)


# -------------------------
# Decoratore di Iniezione
# -------------------------


def add_stats_properties(cls: type[TournamentPlayer]) -> type[TournamentPlayer]:
    """
    Decoratore per arricchire la classe TournamentPlayer.

    Inietta le funzioni di calcolo trasformandole in proprietà memoizzate.
    
    Perché cached_property?
    Questi valori non cambiano durante il ciclo di vita della Request HTTP.
    Calcolarli una volta sola e salvarli in `self.__dict__` risparmia cicli CPU
    e accessi potenziali alle relazioni SQLAlchemy.

    Args:
        cls: La classe TournamentPlayer da decorare.

    Returns:
        La classe arricchita con .total_spent e .tournament_profit.
    """
    cls.total_spent = cached_property(total_spent)
    cls.tournament_profit = cached_property(tournament_profit)
    return cls