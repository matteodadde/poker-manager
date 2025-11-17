"""
Development configuration (LOCAL development environment).

Compatibile al 100% con:
- .env.local
- Setup Windows/macOS via Set-Dev.ps1
- Postgres locale OPPURE fallback SQLite
- Redis opzionale (local redis://, oppure memory://)
- docker-compose (quando avviato manualmente)

Obiettivo: esperienza di sviluppo semplice, immediata, e totalmente coerente
con l'ambiente di produzione — ma con più strumenti di debug.
"""

import os
import logging
from app.config.base import Config, BASE_DIR

log = logging.getLogger(__name__)


class DevelopmentConfig(Config):
    """
    Configurazione per sviluppo locale.
    """

    # ---------------------------
    # ENV & DEBUG
    # ---------------------------
    ENV = "development"
    DEBUG = True
    TESTING = False

    # ---------------------------
    # DATABASE
    # ---------------------------
    # Priorità:
    # 1. DATABASE_URL (da .env.local → Postgres locale o container)
    # 2. DEV_DATABASE_URI (alternativa opzionale)
    # 3. SQLite fallback (sviluppo immediato senza Postgres)
    # ---------------------------

    default_sqlite_path = BASE_DIR / "instance" / "poker_dev.db"

    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL") or
        os.getenv("DEV_DATABASE_URI") or
        f"sqlite:///{default_sqlite_path.resolve()}"
    )

    log.info(f"[Development] Database URI selezionato: {SQLALCHEMY_DATABASE_URI}")

    SQLALCHEMY_ECHO = (
        os.getenv("SQLALCHEMY_ECHO", "False").lower()
        in ("1", "true", "yes")
    )

    # ---------------------------
    # REDIS / LIMITER STORAGE
    # ---------------------------
    # Supporta:
    # - redis://127.0.0.1 → Redis locale
    # - memory:// → fallback automatico
    # - Valore da .env.local
    # ---------------------------

    REDIS_URL = os.getenv("REDIS_URL", "memory://")
    FLASK_LIMITER_STORAGE = os.getenv("FLASK_LIMITER_STORAGE", "memory://")

    log.info(f"[Development] Redis URL: {REDIS_URL}")
    log.info(f"[Development] Limiter Storage: {FLASK_LIMITER_STORAGE}")

    # ---------------------------
    # LOGGING
    # ---------------------------
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

    # ---------------------------
    # COOKIE & SICUREZZA (HTTP locale)
    # ---------------------------
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    # Default scheme (http in locale)
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "http")

    # In sviluppo manteniamo CSRF attivo (best practice)
    WTF_CSRF_ENABLED = True
