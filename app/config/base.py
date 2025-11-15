# app/config/base.py
"""
Configurazione Base dell'Applicazione.

Questo file definisce la classe Config, da cui ereditano:
- DevelopmentConfig
- ProductionConfig
- TestingConfig

La configurazione è compatibile con:
- .env.local (sviluppo locale)
- .env.production (docker/produzione)
- Docker Compose aggiornato
- Rate Limiter (Redis o memory://)
- PostgreSQL locale o container
"""

import os
import secrets
import logging
from pathlib import Path

# Logging durante il bootstrap (prima che Flask configuri il logger)
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger("app.config.base")

# -------------------------------------------------------
# 1. BASE_DIR → percorso assoluto del progetto
# -------------------------------------------------------
try:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
except Exception as e:
    raise RuntimeError(f"Impossibile determinare BASE_DIR: {e}")

# -------------------------------------------------------
# 2. CONFIGURAZIONE BASE (eredita tutto)
# -------------------------------------------------------
class Config:
    """Configurazione base condivisa."""

    # ---------------------------------------------------
    # SICUREZZA — SECRET KEY
    # ---------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        log.warning(
            "AVVISO: SECRET_KEY non trovata — generazione chiave temporanea. "
            "NON usare in produzione!"
        )
        SECRET_KEY = secrets.token_hex(32)

    # ---------------------------------------------------
    # RATE LIMITER (Redis o fallback memory://)
    # ---------------------------------------------------
    RATELIMIT_STORAGE_URL = os.getenv("FLASK_LIMITER_STORAGE")
    REDIS_URL = os.getenv("REDIS_URL")

    if not RATELIMIT_STORAGE_URL:
        if REDIS_URL:
            RATELIMIT_STORAGE_URL = REDIS_URL
        else:
            log.warning("Limiter senza Redis → fallback in-memory.")
            RATELIMIT_STORAGE_URL = "memory://"

    # ---------------------------------------------------
    # SICUREZZA PASSWORD
    # ---------------------------------------------------
    BCRYPT_LOG_ROUNDS = int(os.getenv("BCRYPT_LOG_ROUNDS", 12))

    # ---------------------------------------------------
    # FLASK CORE
    # ---------------------------------------------------
    DEBUG = False
    TESTING = False
    SERVER_NAME = os.getenv("SERVER_NAME")
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "http")

    # ---------------------------------------------------
    # DATABASE SQLAlchemy
    # ---------------------------------------------------
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() in ("1", "true", "yes")

    if not SQLALCHEMY_DATABASE_URI:
        log.error("DATABASE_URL non impostato — impossibile connettersi al DB.")

    # ---------------------------------------------------
    # CSRF / SESSIONE
    # ---------------------------------------------------
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)

    # Cookie policy unificata
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("1", "true", "yes")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = os.getenv("REMEMBER_COOKIE_SECURE", "False").lower() in ("1", "true", "yes")
    REMEMBER_COOKIE_SAMESITE = os.getenv("REMEMBER_COOKIE_SAMESITE", "Lax")
    REMEMBER_COOKIE_DURATION = int(
        os.getenv("REMEMBER_COOKIE_DURATION_SECONDS", 60 * 60 * 24 * 30)
    )

    # ---------------------------------------------------
    # LOGGING
    # ---------------------------------------------------
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # ---------------------------------------------------
    # METADATA APP
    # ---------------------------------------------------
    APP_NAME = os.getenv("APP_NAME", "Poker Tournament Manager")

    # Accesso comodo alla root del progetto
    BASE_DIR = BASE_DIR

# --- Configurazione Avatar ---
    AVATAR_SAVE_PATH = BASE_DIR / "app" / "static" / "images" / "players"
    AVATAR_PUBLIC_URL = "/static/images/players/"
    AVATAR_FINAL_SIZE = 256 
    AVATAR_FULL_SIZE = 800  # <-- AGGIUNGI QUESTA RIGA
    AVATAR_MAX_ORIGINAL_DIMENSION = 3000
    AVATAR_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
    # ---------------------------