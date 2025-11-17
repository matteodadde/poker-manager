# app/models/player/validators.py
"""
Modulo di Validazione Dati (Business Logic Layer).

Questo modulo contiene funzioni "pure" per la validazione sintattica dei dati di input.
Le funzioni qui definite sono disaccoppiate dal modello SQLAlchemy per due motivi:
1. Prevenzione Import Circolari: Il modello usa i validatori, ma i validatori non devono importare il modello.
2. Riutilizzabilità: Queste funzioni possono essere usate ovunque (API, WTF Forms, script di importazione).

Ogni funzione accetta un input grezzo, esegue la sanitizzazione (strip/lower) e restituisce
il dato pulito o solleva un ValueError.
"""

import re
from typing import Optional

# NOTA ARCHITETTURALE:
# Manteniamo questo file privo di dipendenze da 'app.models' o 'app.db'.
# Questo garantisce che la logica di validazione sia testabile in isolamento.


def validate_name(value: str, field_name: str) -> str:
    """
    Valida campi anagrafici (Nome, Cognome).

    Regole:
    - Non può essere vuoto o None.
    - Max 50 caratteri (limite standard database).
    - Non può contenere numeri (solo caratteri alfabetici, spazi, o simboli come apostrofi).

    Args:
        value (str): Il valore da validare.
        field_name (str): Il nome del campo (usato nel messaggio di errore).

    Returns:
        str: La stringa sanitizzata (senza spazi eccessivi ai lati).

    Raises:
        ValueError: Se una delle regole viene violata.
    """
    if not value or not value.strip():
        raise ValueError(f"Il {field_name} non può essere vuoto")
    
    # Sanitizzazione immediata: Rimuove spazi bianchi accidentali (es. copia-incolla)
    cleaned = value.strip()
    
    if len(cleaned) > 50:
        raise ValueError(f"Il {field_name} non può superare i 50 caratteri")
    
    # Controllo integrità: I nomi propri generalmente non contengono cifre.
    # Nota: Questo permette caratteri speciali e accentati, bloccando solo i numeri [0-9].
    if any(char.isdigit() for char in cleaned):
        raise ValueError(f"Il {field_name} non può contenere numeri")
        
    return cleaned


def validate_nickname_rules(value: str) -> str:
    """
    Valida il formato del Nickname (Handle utente).

    Regole:
    - Lunghezza: 3-50 caratteri.
    - Charset: Alfanumerici, punti, trattini bassi, trattini (Regex: ^[\w.-]+$).
    
    NOTA: Questo validatore controlla solo la SINTASSI.
    Il controllo di UNICITÀ (se il nickname è già preso) deve essere fatto a livello di DB/Service.

    Args:
        value (str): Il nickname proposto.

    Returns:
        str: Il nickname sanitizzato.
    """
    if not value or not value.strip():
        raise ValueError("Il nickname non può essere vuoto")
    
    cleaned = value.strip()
    
    # Enforcement dei limiti di lunghezza per UX e DB storage
    if len(cleaned) < 3 or len(cleaned) > 50:
        raise ValueError("Il nickname deve essere tra 3 e 50 caratteri")
    
    # Regex White-list:
    # \w = [a-zA-Z0-9_] (in Python 3 include anche caratteri Unicode se non specificato diversamente)
    # .  = punto letterale
    # -  = trattino
    if not re.match(r"^[\w.-]+$", cleaned):
        raise ValueError(
            "Il nickname può contenere solo lettere, numeri, '.', '_' o '-'"
        )
    return cleaned


def validate_email_format(value: str) -> str:
    """
    Valida il formato dell'indirizzo Email.

    Esegue anche la normalizzazione (lowercase) che è fondamentale per
    evitare duplicati case-sensitive nel database (User@Ex.com == user@ex.com).

    Args:
        value (str): L'email da validare.

    Returns:
        str: L'email normalizzata (minuscola e strippata).
    """
    if not value or not value.strip():
        raise ValueError("L'email non può essere vuota")
    
    # Normalizzazione: Lowercase è standard de-facto per le email nel DB identity.
    cleaned = value.strip().lower()
    
    if len(cleaned) > 120:
        raise ValueError("L'email non può superare i 120 caratteri")
        
    # Validazione Regex:
    # Questa è una "Sanity Check Regex". Non copre il 100% della RFC 5322 (che è complessissima),
    # ma copre il 99% dei casi reali e previene errori di battitura grossolani.
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", cleaned):
        raise ValueError("Formato email non valido")
        
    return cleaned


def validate_password_strength(password: str):
    """
    Applica la policy di complessità della password (NIST guidelines semplificate).

    Attuale Policy:
    - Lunghezza minima: 8 caratteri.
    
    Args:
        password (str): La password in chiaro.

    Returns:
        bool: True se valida.

    Raises:
        ValueError: Se la password è troppo debole.
    """
    if not password:
        raise ValueError("La password non può essere vuota")
        
    # La lunghezza è il fattore più critico per l'entropia.
    if len(password) < 8:
        raise ValueError("La password deve essere di almeno 8 caratteri")
        
    # --- Estendibilità Futura ---
    # Le righe seguenti sono commentate ma pronte all'uso se si volesse
    # imporre una complessità maggiore (es. PCI-DSS compliance).
    # Attualmente disabilitate per non peggiorare la UX in fase di sviluppo/early-stage.
    
    # if not re.search(r"\d", password):
    #     raise ValueError("La password deve contenere almeno un numero")
    # if not re.search(r"[A-Z]", password):
    #     raise ValueError("La password deve contenere almeno una maiuscola")
    
    return True


def validate_country(value: Optional[str]) -> Optional[str]:
    """
    Valida il Codice Paese (ISO 3166-1 alpha-2).

    Accetta None o stringa vuota (campo opzionale).
    Se presente, deve essere esattamente di 2 lettere.

    Args:
        value (Optional[str]): Il codice paese (es. 'it', 'IT', 'us').

    Returns:
        Optional[str]: Il codice paese normalizzato in MAIUSCOLO (es. 'IT') o None.
    """
    if value:
        # Normalizzazione: ISO codes sono sempre uppercase.
        val = value.strip().upper()
        
        if not val:  # Gestisce il caso di stringa contenente solo spazi "   "
            return None
            
        # Regex stretta: Esattamente 2 lettere A-Z.
        if not re.match(r"^[A-Z]{2}$", val):
            raise ValueError(
                "Il codice paese deve essere un codice ISO a 2 lettere (es. IT)"
            )
        return val
        
    return None