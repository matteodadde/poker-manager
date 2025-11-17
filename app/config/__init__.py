# app/config/__init__.py
"""
Inizializzazione del pacchetto di configurazione.

Questo modulo agisce come 'Factory' per la configurazione dell'applicazione.
Le sue responsabilità principali sono:
1. Identificare l'ambiente di esecuzione (Development, Production, Testing).
2. Istanziare la classe di configurazione appropriata.
3. Eseguire validazioni critiche *post-inizializzazione* (sanity checks).
4. Esportare l'istanza `config` pronta per essere consumata dall'applicazione Flask.

Pattern: Strategy (selezione della classe) + Fail Fast (validazione immediata).
"""
import os
import logging

# Import delle classi di configurazione specifiche.
# Ogni modulo gestisce le variabili specifiche per quell'ambiente.
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig  # Import necessario per l'ambiente di CI/CD

# Configurazione base del logging per questa fase critica di bootstrap.
# NOTA: Usiamo basicConfig qui per garantire che eventuali errori di configurazione
# vengano stampati su stdout/stderr anche se il logger dell'app non è ancora pronto.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger(__name__)  # Logger con namespace specifico per tracciare l'origine

# --- 1. Determinazione della Classe di Configurazione ---
# Leggiamo la variabile d'ambiente standard per definire il contesto.
raw_flask_env = os.getenv("FLASK_ENV")
log.debug(f"Letto FLASK_ENV dall'ambiente: {raw_flask_env!r}")

# Normalizzazione dell'input:
# - Gestisce spazi vuoti accidentali.
# - Converte in minuscolo per consistenza.
# - Default a 'development' se la variabile manca o è vuota (Safety default).
env = (
    raw_flask_env.strip().lower()
    if raw_flask_env and raw_flask_env.strip()
    else "development"
)
log.info(f"Ambiente effettivo selezionato basato su FLASK_ENV: '{env}'")

# Mapping esplicito stringa -> Classe.
# Questo permette di estendere facilmente nuovi ambienti in futuro.
config_class_mapping = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

ConfigClass = config_class_mapping.get(env)

# Gestione Fallback:
# Se l'ambiente specificato non esiste nella mappa, torniamo a Development
# ma emettiamo un warning per avvisare l'operatore del disallineamento.
if not ConfigClass:
    log.warning(
        f"Valore FLASK_ENV sconosciuto o non valido: '{raw_flask_env}'. "
        f"Verrà utilizzata la configurazione di default: DevelopmentConfig."
    )
    ConfigClass = DevelopmentConfig
    env = "development"  # Forziamo l'ambiente per riflettere la scelta reale

# --- 2. Istanziazione della Configurazione ---
try:
    log.info(f"Tentativo di istanziazione della classe: {ConfigClass.__name__}")
    # Qui viene eseguito l'__init__ della classe specifica (es. caricamento .env)
    config = ConfigClass()
    log.info(f"Istanziazione completata con successo: {ConfigClass.__name__}")
except Exception as e:
    # Se la classe di config fallisce nel suo __init__, è un errore irrecuperabile.
    log.critical(
        f"ERRORE FATALE: Errore inatteso durante l'inizializzazione di {ConfigClass.__name__}: {e}",
        exc_info=True,
    )
    # Rilanciamo come RuntimeError per fermare l'avvio dell'applicazione (Fail Fast).
    raise RuntimeError(
        f"Impossibile istanziare la classe di configurazione {ConfigClass.__name__}: {e}"
    )

# --- 3. VALIDAZIONI CRITICHE (Post-Istanziazione) ---
# Questi controlli sono agnostici rispetto alla classe caricata.
# Servono a garantire che l'app non parta in uno stato instabile o insicuro.

validation_errors = []

# A. Validazione SECRET_KEY
# La chiave è fondamentale per la firma delle sessioni e la sicurezza CSRF.
if not config.SECRET_KEY:
    if env != "testing":  # In Testing potremmo non averne bisogno o usarne una fittizia
        validation_errors.append(
            "SECRET_KEY mancante. Controllare il file .env o le variabili d'ambiente."
        )
    else:
        log.warning("SECRET_KEY mancante, ma permesso in ambiente di testing.")
elif (
    len(config.SECRET_KEY) < 16 and env != "testing"
):  # Enforcement sulla lunghezza minima
    log.warning(
        "AVVISO SICUREZZA: La SECRET_KEY è inferiore a 16 caratteri. Dovrebbe essere una stringa lunga e casuale."
    )
    # validation_errors.append("SECRET_KEY is too short.") # Scommentare per rendere l'errore bloccante

# B. Validazione DATABASE URI
# Verifichiamo che la stringa di connessione al DB esista.
db_uri = getattr(config, "SQLALCHEMY_DATABASE_URI", None)  # Accesso sicuro
if not db_uri:
    if env == "production":
        # In produzione è inaccettabile non avere un DB configurato.
        msg = "La variabile d'ambiente DATABASE_URL non è impostata."
        validation_errors.append(msg)
    elif env == "development":
        # In dev, DevelopmentConfig dovrebbe averne calcolato uno di default (sqlite).
        msg = "SQLALCHEMY_DATABASE_URI mancante in sviluppo. Controllare DEV_DATABASE_URI o il calcolo del percorso di default."
        validation_errors.append(msg)
    elif env == "testing":
        # In testing, il DB viene spesso iniettato dai fixture (conftest.py),
        # quindi emettiamo solo un warning invece di bloccare.
        log.warning(
            "SQLALCHEMY_DATABASE_URI non impostato al caricamento config per testing. Assicurarsi che il setup dei test (es. conftest.py) lo configuri."
        )
    else:
        msg = f"SQLALCHEMY_DATABASE_URI mancante per l'ambiente '{env}'."
        validation_errors.append(msg)
else:
    # C. Fix compatibilità SQLAlchemy <-> Provider PaaS (es. Heroku/Render)
    # Molti provider esportano ancora l'URL con prefisso 'postgres://',
    # ma le versioni recenti di SQLAlchemy richiedono 'postgresql://'.
    if isinstance(db_uri, str) and db_uri.startswith("postgres://"):
        # Modifica "in-place" sull'istanza di configurazione
        config.SQLALCHEMY_DATABASE_URI = db_uri.replace(
            "postgres://", "postgresql://", 1
        )
        log.info(
            "Schema SQLALCHEMY_DATABASE_URI corretto automaticamente da 'postgres://' a 'postgresql://'."
        )

# --- 4. Controllo Finale e Chiusura ---
if validation_errors:
    # Loggiamo ogni errore singolarmente per chiarezza
    for error in validation_errors:
        log.critical(f"Errore Configurazione: {error}")
    # Blocchiamo l'esecuzione. È meglio crashare subito che avere comportamenti indefiniti.
    raise ValueError(
        f"Validazione critica della configurazione fallita: {'; '.join(validation_errors)}"
    )
else:
    log.info(
        f"Configurazione caricata e validata con successo per l'ambiente '{env}'."
    )


# Esportiamo l'istanza configurata ('config') rendendola disponibile all'app factory.
# Questo è l'unico oggetto che il resto dell'app dovrebbe importare da questo package.
__all__ = ["config"]