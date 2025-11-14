# app/__init__.py

"""
Main application package initializer.

This file initializes the core Flask extensions
(like SQLAlchemy, Migrate, Bcrypt, LoginManager)
as empty instances.

These instances are then configured and linked
to the Flask app instance by the factory in 'app_factory.py'.
"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address  # Helper per il rate limiting

# Example: Import other extensions if needed
# from flask_mail import Mail

# --- CREATE EXTENSION INSTANCES ---
# These are the single instances that the entire application will use.
# They are initialized here but configured ('init_app') in the app factory.
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()

# Aggiunto Limiter per il Rate-Limiting (sicurezza brute-force)
# Usa get_remote_address per tracciare gli IP
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "redis://redis:6379/0"),  # Assumendo che Redis sia in esecuzione localmente
    # Puoi impostare un default globale qui, se vuoi,
    # o lasciarlo vuoto per definirlo solo sulle route.
    # default_limits=["200 per day", "50 per hour"]
)


# Optional: Add other extensions here if needed
# mail = Mail()

# Ensure that models are imported somewhere BEFORE Flask-Migrate or db operations
# occur outside the factory context (usually handled by importing in the factory).
# No imports needed here if the factory handles all model imports reliably.
