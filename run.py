# run.py
"""
Main script for the Flask application.

Loads environment variables and creates the application instance
using the factory pattern. The 'app' instance created here is
automatically discovered by the 'flask run' command.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# --- Load Environment Variables ---
# Carica il .env SOLO se non siamo in un ambiente (come Docker)
# che ha già impostato le variabili per noi.
if not os.getenv("DATABASE_URL"):
    try:
        if load_dotenv():
            print("run.py: Variabili d'ambiente caricate da .env (modalità locale)")
        else:
            print("run.py: .env non trovato.")
    except Exception as e:
        print(f"run.py: Errore caricamento .env: {e}")
else:
    print(
        "run.py: Variabili d'ambiente già presenti (Docker Compose). Salto caricamento .env."
    )

# Use basic logging until app logger is ready
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger(__name__)

# --- Create Global App Instance ---
try:
    from app_factory import create_app
except ImportError:
    log.critical(
        "FATAL ERROR: Could not find 'app_factory.py'. Ensure it's in the project root."
    )
    sys.exit(1)

# Create the Flask app instance. This is what 'flask run' will use.
try:
    app = create_app(is_testing=False)
    # Use app's logger if available, otherwise basic log
    logger = app.logger if hasattr(app, "logger") else log
    logger.info("run.py: Flask app instance created successfully by factory.")

except Exception as e:
    log.critical(f"FATAL ERROR during Flask app creation: {e}", exc_info=True)
    sys.exit(1)