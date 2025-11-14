# app/models/tournament_player/validators.py

"""
Modulo di Validazione Partecipazione (Business Logic Layer).

Questo modulo gestisce l'integrità dei dati relativi alla performance di un giocatore in un torneo.
Oltre ai controlli di tipo (Type Checking), implementa validazioni "Contestuali":
verifica la coerenza logica tra i rebuy effettuati e la spesa dichiarata, basandosi
sulle regole del torneo padre (se disponibile).

Le funzioni sono progettate per essere robuste:
- Sanitizzano gli input (`None` -> `0`).
- Gestiscono conversioni finanziarie sicure (`Decimal`).
- Emettono warning invece di errori bloccanti quando rilevano anomalie non critiche.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    # Import solo per annotazioni di tipo statico (evita cicli a runtime)
    from app.models.tournament_player.base import TournamentPlayer


def validate_rebuy(value: Optional[int]) -> int:
    """
    Valida il contatore dei Rebuy.

    Regole:
    - Deve essere un intero.
    - Deve essere >= 0 (non esistono rebuy negativi).
    - Input `None` viene normalizzato a `0` (default sicuro).

    Args:
        value: Il numero di rebuy o None.

    Returns:
        int: Il valore intero sanitizzato.
    """
    if value is None:
        return 0

    try:
        value_int = int(value)
    except (ValueError, TypeError):
        raise ValueError("Il numero di rebuy deve essere un intero.")

    if value_int < 0:
        raise ValueError("Il numero di rebuy deve essere non negativo.")
    return value_int


def validate_rebuy_total_spent(
    instance: "TournamentPlayer", value: Union[Decimal, float, str, None]
) -> Decimal:
    """
    Valida la spesa totale per i Rebuy con controllo di coerenza (Cross-Validation).

    Questa funzione non guarda solo il valore in sé, ma ispeziona l'istanza `TournamentPlayer`
    per verificare se la spesa ha senso rispetto al numero di rebuy dichiarati e al buy-in del torneo.

    Logica Euristica:
    - Se rebuy == 0 -> La spesa DEVE essere 0.
    - Se rebuy > 0 -> Controlla se la spesa corrisponde a multipli del buy-in (Full Price)
      o della metà del buy-in (Half Price - regola comune in molti tornei).
      Se non corrisponde, logga un WARNING ma non blocca l'esecuzione (permette override manuali).

    Args:
        instance (TournamentPlayer): L'oggetto che si sta validando (per accedere a .rebuy e .tournament).
        value: L'importo speso.

    Returns:
        Decimal: L'importo validato e formattato a 2 decimali.
    """
    # Normalizzazione: None diventa 0.00 soldi
    if value is None:
        return Decimal("0.00")

    try:
        # Conversione finanziaria sicura
        decimal_value = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(
            "Il totale speso per i rebuy deve essere un numero decimale valido."
        )

    if decimal_value < 0:
        raise ValueError("Il totale speso per i rebuy non può essere negativo.")

    # --- Logica di Controllo Contestuale ---
    # Verifichiamo che l'istanza abbia i dati necessari (torneo caricato) per fare calcoli avanzati.
    if (
        hasattr(instance, "rebuy")
        and hasattr(instance, "tournament")
        and instance.tournament is not None
        and instance.tournament.buy_in is not None
    ):
        # Recuperiamo il numero di rebuy (già validato in precedenza o 0)
        rebuy_count = instance.rebuy

        # Caso 1: Incoerenza Logica Grave.
        # Non puoi aver speso soldi per rebuy se il contatore rebuy è zero.
        if rebuy_count == 0 and decimal_value != Decimal("0.00"):
            raise ValueError(
                "Se non ci sono rebuy, l'importo speso per rebuy deve essere zero."
            )

        # Caso 2: Audit del Costo (Soft Validation).
        # Se ci sono rebuy, verifichiamo se il prezzo pagato è "standard".
        if rebuy_count > 0:
            # Calcolo dei due scenari di prezzo più comuni:
            # 1. Half Price: Il rebuy costa metà del buy-in (es. Tornei con add-on scontati).
            # 2. Full Price: Il rebuy costa quanto il buy-in (es. Freezeout con rientri).
            half_price = (instance.tournament.buy_in / 2).quantize(Decimal("0.01"))
            full_price = instance.tournament.buy_in.quantize(Decimal("0.01"))

            possible_values = [
                (rebuy_count * half_price).quantize(Decimal("0.01")),
                (rebuy_count * full_price).quantize(Decimal("0.01")),
            ]

            # Se il valore inserito non corrisponde a nessuno dei due standard,
            # emettiamo un Warning nei log. Non solleviamo eccezione perché l'admin
            # potrebbe aver applicato uno sconto manuale o una penalità specifica.
            if (
                decimal_value != possible_values[0]
                and decimal_value != possible_values[1]
            ):
                logging.warning(
                    f"Costo rebuy ({decimal_value}) non standard per {rebuy_count} rebuy. "
                    f"Valori attesi: {possible_values[0]} (Half) o {possible_values[1]} (Full)"
                )

    return decimal_value


def validate_posizione(value: Optional[int]) -> Optional[int]:
    """
    Valida la posizione finale in classifica.

    Regole:
    - Deve essere un intero positivo (>= 1).
    - `None` è un valore valido (indica giocatore non classificato, eliminato senza rank, o torneo in corso).

    Returns:
        Optional[int]: La posizione o None.
    """
    if value is None:
        return None

    try:
        value_int = int(value)
    except (ValueError, TypeError):
        raise ValueError("La posizione deve essere un intero.")

    if value_int < 1:
        raise ValueError(
            "La posizione deve essere un intero positivo (maggiore o uguale a 1)."
        )
    return value_int


def validate_prize(value: Union[Decimal, float, str, None]) -> Optional[Decimal]:
    """
    Valida il premio vinto (Payout).

    Regole:
    - Accetta `None` (significa "Non a premio" / "Out of the money").
    - Se presente, deve essere >= 0.

    Returns:
        Optional[Decimal]: Il premio formattato o None.
    """
    if value is None:
        return None
    try:
        decimal_value = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Il premio deve essere un numero non negativo valido.")
    if decimal_value < 0:
        raise ValueError("Il premio deve essere un numero non negativo valido.")
    return decimal_value