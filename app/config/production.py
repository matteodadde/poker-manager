# app/config/production.py

"""
Configurazione per l’ambiente di Produzione (Production).

Allineato al 100% con:
- Docker Compose
- .env.production
- Architettura della webapp
- Sicurezza e best practices reali

Funzionalità incluse:
- Debug OFF
- Uso di Postgres (servizio 'db')
- Redis per sessioni + rate limiting
- Fallback automatici se mancano servizi
- Cookie sicuri, HTTPS-aware
"""

import os
import logging
from app.config.base import Config

log = logging.getLogger(__name__)


class ProductionConfig(Config):
    """Configurazione Flask specifica per l'ambiente Production."""

    # Identificatore ambiente
    ENV = "production"

    # Debug SEMPRE off
    DEBUG = False
    TESTING = False

    # Livello di logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    # ============================
    # 🔥 DATABASE (PostgreSQL)
    # ============================
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("[Production] DATABASE_URL mancante! Controlla .env.production o Docker Compose.")

    SQLALCHEMY_ECHO = False  # niente query log

    # ============================
    # 🔐 SECRET KEY
    # ============================
    # Validata in config/__init__.py
    SECRET_KEY = os.getenv("SECRET_KEY")

    # ============================
    # 🍪 COOKIE SECURITY
    # ============================
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    REMEMBER_COOKIE_SAMESITE = os.getenv("REMEMBER_COOKIE_SAMESITE", "Lax")

    # ============================
    # 🌐 URL / PROXY / HTTPS
    # ============================
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https")

    # Supporto reverse proxy (es: NGINX)
    USE_PROXY_FIX = True

    # ============================
    # 🚦 RATE LIMITING (Redis)
    # ============================
    LIMITER_STORAGE_URI = os.getenv("FLASK_LIMITER_STORAGE", "memory://")

    if LIMITER_STORAGE_URI.startswith("redis://"):
        log.info(f"[Production] Rate limiting con Redis → {LIMITER_STORAGE_URI}")
    else:
        log.warning(
            "[Production] Redis NON configurato. "
            "Uso fallback memory:// → nessuna persistenza del rate limiter."
        )

    # ============================
    # 📦 REDIS (sessioni e caching)
    # ============================
    REDIS_URL = os.getenv("REDIS_URL")

    if not REDIS_URL:
        log.warning("[Production] REDIS_URL mancante! Sessioni e caching useranno fallback interno.")
    else:
        log.info(f"[Production] Redis attivo per sessioni → {REDIS_URL}")

    # ============================
    # 🔐 CSRF Protection
    # ============================
    WTF_CSRF_ENABLED = True

    # ============================
    # ⭐ NOTE
    # - SECRET_KEY e DATABASE_URL vengono validati automaticamente
    #   dentro config/__init__.py → la tua codebase è già sicura
    # ============================
