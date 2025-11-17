# app/models/tournament/validators.py

"""
Modulo di Validazione Dati Torneo.

Questo modulo contiene funzioni "pure" per la validazione e la normalizzazione
dei dati in input per l'entità Tournament.

Principi Architetturali:
1.  **Statelessness**: Le funzioni non dipendono dal contesto DB o Flask.
2.  **Type Coercion**: Converte input eterogenei (str, float) in tipi Python forti (Decimal, Date).
3.  **Data Integrity**: Garantisce che nel DB finiscano solo dati conformi alle regole di business.

Questo layer agisce da "Gatekeeper" prima che i dati tocchino il modello SQLAlchemy.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Union


def validate_name(value: str) -> str:
    """
    Valida e sanitizza il nome del torneo.

    Regole:
    - Obbligatorio (non None, non vuoto).
    - Max 100 caratteri (vincolo schema DB).
    - Trim degli spazi bianchi (evita " Nome " vs "Nome").

    Args:
        value (str): Nome grezzo.

    Returns:
        str: Nome pulito.

    Raises:
        ValueError: Se il vincolo di lunghezza o presenza è violato.
    """
    if not value or not value.strip():
        raise ValueError("Il nome del torneo non può essere vuoto.")

    cleaned = value.strip()
    
    # Controllo lunghezza per evitare troncamenti silenziosi o errori DB (Data Truncation).
    if len(cleaned) > 100:
        raise ValueError("Il nome del torneo non può superare i 100 caratteri.")
    return cleaned


def validate_buy_in(value: Union[Decimal, float, str]) -> Decimal:
    """
    Valida e converte il Buy-in (Costo di iscrizione).

    Gestione Finanziaria:
    - Converte tutto in `Decimal` per evitare errori di virgola mobile (Floating Point Arithmetic).
    - Passa attraverso `str(value)` prima di Decimal() per best practice.
    - Forza 2 decimali (`quantize`) per standard valutario.

    Args:
        value: Input numerico o stringa.

    Returns:
        Decimal: Valore monetario validato (es. 10.00).

    Raises:
        ValueError: Se <= 0 o formato non valido.
    """
    try:
        # Conversione robusta: Decimal('10.5') è sicuro, Decimal(10.5) float può avere artefatti.
        value = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError("Il buy-in deve essere un numero decimale valido.")
    
    # Business Rule: Un torneo deve avere un costo > 0.
    # (Per tornei gratuiti/freeroll, la logica potrebbe dover cambiare qui in futuro).
    if value <= 0:
        raise ValueError("Il buy-in deve essere maggiore di zero.")
        
    return value.quantize(Decimal("0.01"))


def validate_prize_pool(value: Union[Decimal, float, str, None]) -> Decimal | None:
    """
    Valida il Montepremi Garantito/Iniziale.

    Differenze rispetto al Buy-in:
    - Può essere None (se calcolato dinamicamente in base agli iscritti).
    - Può essere 0 (es. torneo for fun o satellite senza cash prize immediato).

    Args:
        value: Input numerico, stringa o None.

    Returns:
        Decimal | None: Il montepremi formattato o None.
    """
    if value is None:
        return None
    try:
        value = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError("Il prize_pool deve essere un numero decimale valido.")
        
    # Business Rule: Non esistono montepremi negativi.
    if value < 0:
        raise ValueError("Il prize_pool non può essere negativo.")
        
    return value.quantize(Decimal("0.01"))


def validate_location(value: Union[str, None]) -> Union[str, None]:
    """
    Valida la location (Luogo dell'evento).

    Normalizzazione:
    - Converte stringhe vuote o di soli spazi in `None` (NULL su DB).
    - Questo migliora la coerenza dei dati (evita mix di NULL e "").

    Args:
        value: Location grezza.

    Returns:
        str | None: Location pulita o None.
    """
    if value is None:
        return None

    cleaned = value.strip()
    
    # Se l'utente invia "   ", lo trattiamo come dato mancante -> None
    if not cleaned:
        return None

    if len(cleaned) > 150:
        raise ValueError("La location non può superare i 150 caratteri.")
    return cleaned


def validate_tournament_date(value: Union[date, datetime]) -> date:
    """
    Valida e normalizza la data del torneo.

    Adapter Pattern:
    Accetta diversi formati in input (datetime, date, stringa ISO da API/JSON)
    e restituisce uniformemente un oggetto `date` standard Python.

    Args:
        value: Data in vari formati.

    Returns:
        date: Oggetto date puro (senza orario).

    Raises:
        ValueError: Se il formato è irriconoscibile.
    """
    # Caso 1: È già un datetime (es. da SQLAlchemy o form datetime-local). Estraiamo la data.
    if isinstance(value, datetime):
        return value.date()
        
    # Caso 2: È già un date (caso ideale).
    if isinstance(value, date):
        return value

    # Caso 3: È una stringa (es. payload JSON API o form HTML grezzo).
    # Tentiamo il parsing ISO 8601 (YYYY-MM-DD).
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            # Fallthrough all'errore generico
            pass

    raise ValueError(
        "La data del torneo deve essere un oggetto 'date', 'datetime' "
        "o una stringa in formato ISO (YYYY-MM-DD)."
    )