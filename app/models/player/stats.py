# app/models/player/stats.py
"""
Modulo Statistiche Giocatore.

Questo modulo contiene la logica di business per il calcolo delle metriche di performance
dei giocatori (ROI, ITM%, Profitto, ecc.).

Pattern Architetturale: Mixin / Decorator Injection.
Invece di intasare il modello `Player` (in base.py) con decine di metodi di calcolo,
li definiamo qui come funzioni pure e li iniettiamo dinamicamente nella classe Player
usando `cached_property`. Questo garantisce:
1. Performance: I calcoli pesanti vengono eseguiti solo una volta per richiesta.
2. Pulizia: Il file del modello base rimane focalizzato sulla definizione dello schema DB.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional
from werkzeug.utils import cached_property
from sqlalchemy import func, distinct
from app import db
from app.models.tournament_player.base import TournamentPlayer
from app.models.tournament_player.stats import total_spent as tp_total_spent
from app.utils.decimal import round_decimal

# Soglia per considerare un piazzamento come "In The Money" (a premio).
TOP_ITM_POSITION = 4

def total_winnings(self) -> Decimal:
    """
    Calcola il totale Lordo delle vincite (Gross Winnings).
    Non sottrae i costi di iscrizione.
    """
    total = Decimal("0.00")
    # Itera sulle associazioni TournamentPlayer per sommare i premi
    for tp in self.tournament_players:
        if tp.prize is not None:
            total += tp.prize
    return total.quantize(Decimal("0.01"))



def total_spent(self) -> Decimal:
    """
    Calcola l'investimento totale del giocatore.
    Include: Buy-in iniziale + Costo di tutti i Rebuy effettuati.
    """
    total = Decimal("0.00")
    for tp in self.tournament_players:
        # Delega il calcolo del costo singolo al modello TournamentPlayer
        total += tp_total_spent(tp)
    return round_decimal(total)


def num_tournaments(self) -> int:
    """
    Conta il numero di tornei unici a cui il giocatore ha partecipato.
    
    Ottimizzazione SQL: Usa `count(distinct)` direttamente sul DB per evitare
    di caricare in memoria tutte le istanze di TournamentPlayer.
    """
    stmt = db.select(func.count(distinct(TournamentPlayer.tournament_id))).filter(
        TournamentPlayer.player_id == self.id
    )
    count = db.session.scalar(stmt)
    return count or 0


def num_wins(self) -> int:
    """
    Conta il numero di vittorie assolute (1° posto).
    """
    stmt = (
        db.select(func.count())
        .select_from(TournamentPlayer)
        .filter(TournamentPlayer.player_id == self.id, TournamentPlayer.posizione == 1)
    )
    count = db.session.scalar(stmt)
    return count or 0


def win_rate(self) -> Optional[Decimal]:
    """
    Win Rate %.
    Calcola la percentuale di vittorie rispetto ai tornei giocati.
    Restituisce None se non ci sono tornei giocati.
    """
    total_tournaments = self.num_tournaments
    if total_tournaments == 0:
        return None

    # Calcolo percentuale standard
    wins = self.num_wins
    rate = (Decimal(wins) / Decimal(total_tournaments)) * Decimal("100")
    return round_decimal(rate)


def in_the_money(self) -> int:
    """
    Conta i piazzamenti 'In The Money' (ITM).
    Si basa sulla costante `TOP_ITM_POSITION` definita a livello di modulo.
    """
    stmt = (
        db.select(func.count())
        .select_from(TournamentPlayer)
        .filter(
            TournamentPlayer.player_id == self.id,
            TournamentPlayer.posizione.isnot(None), # Esclude chi non ha una posizione (es. DNF)
            TournamentPlayer.posizione <= TOP_ITM_POSITION,
        )
    )
    count = db.session.scalar(stmt)
    return count or 0


def itm_rate(self) -> Optional[Decimal]:
    """
    ITM %.
    Calcola la frequenza con cui il giocatore va a premio rispetto ai tornei giocati.
    """
    total = self.num_tournaments
    if total == 0:
        return None

    itm = self.in_the_money
    rate = (Decimal(itm) / Decimal(total)) * Decimal("100")
    return round_decimal(rate)


def num_rebuy(self) -> int:
    """
    Volume totale di Rebuy.
    Somma il numero di volte che il giocatore ha fatto rebuy in tutti i tornei.
    NOTA: Qui il calcolo è Python-side. Se il numero di tornei cresce molto,
    potrebbe valere la pena spostarlo su una query SQL `func.sum`.
    """
    return sum(tp.rebuy or 0 for tp in self.tournament_players)


def net_profit(self) -> Decimal:
    """
    Profitto Netto (ROI assoluto).
    Formula: Totale Vincite - (Buy-in + Rebuy).
    Può essere negativo.
    """
    return self.total_winnings - self.total_spent

def roi(self) -> Optional[Decimal]:
    """
    Return on Investment (ROI) %.
    Calcola il ritorno sull'investimento come percentuale del totale speso.
    Restituisce None se il totale speso è zero.
    Formula: (Profitto Netto / Totale Speso) * 100
    """
    total_spent = self.total_spent
    if total_spent == 0:
        return None

    net_profit = self.net_profit
    roi_value = (net_profit / total_spent) * Decimal("100")
    return round_decimal(roi_value)


def avg_profit_per_tournament(self) -> Optional[Decimal]:
    """
    Profitto medio per singolo evento.
    Utile per stimare l'expected value (EV) storico del giocatore.
    """
    total = self.num_tournaments
    if total == 0:
        return None
    try:
        return round_decimal(self.net_profit / total)
    except (
        ValueError,
        TypeError,
        InvalidOperation,
        ZeroDivisionError,
    ):  # pragma: no cover
        # Fail-safe per casi limite aritmetici
        return None  # pragma: no cover


def avg_rebuy_per_tournament(self) -> Optional[float]:
    """
    Indice di Aggressività/Spesa.
    Media dei rebuy effettuati per torneo.
    """
    total = self.num_tournaments
    if total == 0:
        return None

    total_rebuy = self.num_rebuy
    return round(total_rebuy / total, 2)


def avg_prize_when_paid(self) -> Decimal:
    """
    Media vincite (condizionata).
    Calcola quanto vince mediamente il giocatore *solo quando va a premio*.
    Esclude i tornei persi dal calcolo della media.
    """
    premiati = [tp.prize for tp in self.tournament_players if tp.prize and tp.prize > 0]
    if not premiati:
        return Decimal("0.00")
    return round_decimal(sum(premiati) / len(premiati))


def win_to_itm_ratio(self) -> Optional[float]:
    """
    Conversion Rate (ITM -> Win).
    Indica la capacità di chiudere il torneo ("Closer") una volta raggiunta la zona premi.
    Esempio: 0.50 significa che vince metà delle volte che va a premio.
    """
    itm = self.in_the_money
    if itm == 0:
        return None

    wins = self.num_wins
    return round(wins / itm, 2)


def num_zero_rebuy_tournaments(self) -> int:
    """
    Conta i tornei 'Clean'.
    Numero di tornei giocati pagando solo il buy-in iniziale (0 rebuy).
    """
    return sum(1 for tp in self.tournament_players if (tp.rebuy or 0) == 0)

def abi(self) -> Decimal:
    """
    Average Buy-In (ABI).
    Calcola il costo medio del buy-in per torneo.
    """
    total = self.num_tournaments
    if total == 0:
        return Decimal("0.00")
    return round_decimal(self.total_buyin_spent / total)

def cpc(self) -> Decimal:
    """
    Cost Per Cash (CPC).
    Calcola il costo medio sostenuto per ogni piazzamento a premio (ITM).
    """
    itm = self.in_the_money
    if itm == 0:
        return Decimal("0.00")
    return round_decimal(self.total_spent / itm)


def total_buyin_spent(self) -> Decimal:
    """
    Breakdown Spese: Solo Buy-in.
    Somma i costi di ingresso iniziali.
    """
    total = Decimal("0.00")
    for tp in self.tournament_players:
        if tp.tournament and tp.tournament.buy_in:
            total += Decimal(tp.tournament.buy_in)
    return round_decimal(total)


def total_rebuy_spent(self) -> Decimal:
    """
    Breakdown Spese: Solo Rebuy.
    Somma esclusivamente i costi sostenuti per i rientri.
    """
    total = Decimal("0.00")
    for tp in self.tournament_players:
        total += tp.rebuy_total_spent or Decimal("0.00")
    return round_decimal(total)

def rebuy_tournaments(self) -> int:
    """
    Numero di tornei con almeno un rebuy.
    """
    return self.num_tournaments - self.num_zero_rebuy_tournaments

def rebuy_frequency(self) -> Optional[Decimal]:
    """
    Frequenza Rebuy (%).
    Percentuale dei tornei in cui il giocatore ha fatto almeno un rebuy.
    """
    total = self.num_tournaments
    if total == 0:
        return None

    rebuy_tournaments = total - self.num_zero_rebuy_tournaments
    freq = (Decimal(rebuy_tournaments) / Decimal(total)) * Decimal("100")
    return round_decimal(freq)


# -------------------------
# Decoratore di Iniezione
# -------------------------


def add_stats_properties(cls):
    """
    Decoratore per iniettare le statistiche nel modello Player.
    
    Utilizza `werkzeug.utils.cached_property` invece di `@property` standard.
    Questo è cruciale per le performance: il calcolo viene eseguito la prima volta
    che l'attributo viene acceduto e il risultato viene memorizzato nell'istanza
    per la durata della richiesta. Evita di ricalcolare query SQL pesanti se
    la statistica viene letta più volte nel template.
    """
    cls.total_winnings = cached_property(total_winnings)
    cls.total_spent = cached_property(total_spent)
    cls.net_profit = cached_property(net_profit)
    cls.roi = cached_property(roi)
    cls.num_tournaments = cached_property(num_tournaments)
    cls.num_wins = cached_property(num_wins)
    cls.win_rate = cached_property(win_rate)
    cls.in_the_money = cached_property(in_the_money)
    cls.itm_rate = cached_property(itm_rate)
    cls.num_rebuy = cached_property(num_rebuy)
    cls.avg_profit_per_tournament = cached_property(avg_profit_per_tournament)
    cls.avg_rebuy_per_tournament = cached_property(avg_rebuy_per_tournament)
    cls.avg_prize_when_paid = cached_property(avg_prize_when_paid)
    cls.win_to_itm_ratio = cached_property(win_to_itm_ratio)
    cls.num_zero_rebuy_tournaments = cached_property(num_zero_rebuy_tournaments)
    cls.abi = cached_property(abi)
    cls.cpc = cached_property(cpc)
    cls.total_buyin_spent = cached_property(total_buyin_spent)
    cls.rebuy_tournaments = cached_property(rebuy_tournaments)
    cls.total_rebuy_spent = cached_property(total_rebuy_spent)
    cls.rebuy_frequency = cached_property(rebuy_frequency)
    return cls