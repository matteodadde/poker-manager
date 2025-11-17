# app/config/testing.py
"""
Configurazione per l'ambiente di Testing (CI/CD & Unit Tests).

Questo modulo è ottimizzato per due obiettivi principali:
1. VELOCITÀ: Utilizzo di database in memoria e disabilitazione di processi costosi (hashing).
2. ISOLAMENTO: Ogni test deve girare in un ambiente pulito e prevedibile.

Pattern: Mocking dell'infrastruttura (DB in RAM, Rate Limits disabilitati).
"""

# StaticPool è essenziale per SQLite in-memory con SQLAlchemy.
# Mantiene aperta l'unica connessione al DB per evitare che venga distrutta (e i dati persi) tra le query.
from sqlalchemy.pool import StaticPool
from app.config.base import Config


class TestingConfig(Config):
    """
    Configurazione specifica per l'esecuzione dei test automatizzati (pytest/unittest).
    """

    # --- Rate Limiting ---
    # Usiamo lo storage in memoria per evitare dipendenze da Redis durante i test.
    RATELIMIT_STORAGE_URL = "memory://"
    # Disabilitiamo completamente il rate limiting per evitare "flaky tests"
    # (test che falliscono solo perché eseguiti troppo velocemente dalla CI).
    RATELIMIT_ENABLED = False

    # --- Flag Ambiente ---
    ENV = "testing"
    TESTING = True  # Segnala a Flask di propagare le eccezioni invece di gestirle con error handlers generici.
    DEBUG = False

    # --- Database (In-Memory SQLite) ---
    # Usiamo ':memory:' per creare un DB volatile nella RAM.
    # Vantaggi: Velocità estrema, nessun file residuo su disco, pulizia automatica al termine del processo.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # Opzioni specifiche per far funzionare SQLite in-memory con SQLAlchemy:
    SQLALCHEMY_ENGINE_OPTIONS = {
        # check_same_thread=False: Permette di condividere la connessione tra thread diversi
        # (necessario per alcuni test runner o se si testano componenti async/celery).
        "connect_args": {"check_same_thread": False},
        
        # poolclass=StaticPool: CRUCIALE.
        # Default SQLAlchemy crea e distrugge connessioni. Con SQLite :memory:,
        # chiudere la connessione cancella il DB. StaticPool mantiene viva la connessione
        # per l'intera durata del test session o del contesto app.
        "poolclass": StaticPool,
    }

    # --- Sicurezza (Semplificata per Test) ---
    # Usiamo una chiave fissa e nota per garantire la riproducibilità dei test
    # che dipendono da firme crittografiche (es. token reset password).
    SECRET_KEY = "test-secret-key-for-unit-tests"
    
    # Disabilitiamo la protezione CSRF nei form.
    # Questo semplifica enormemente i test funzionali delle API/Form POST,
    # evitando di dover estrarre e iniettare token CSRF in ogni richiesta di test.
    WTF_CSRF_ENABLED = False

    # --- Performance Hashing ---
    # L'hashing delle password (es. Bcrypt/Argon2) è progettato per essere LENTO (CPU intensive)
    # per resistere al brute-force. In una suite di 1000 test, questo aggiungerebbe minuti di attesa inutile.
    # Impostando questo flag (che l'app deve gestire nel modello User), bypassiamo l'hashing o usiamo un algoritmo banale (MD5/Plain).
    PASSWORD_HASHING_DISABLED = True