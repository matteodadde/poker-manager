# logging_config.py
"""
Configurazione del logging per l'applicazione Flask (Poker 5.0).

Crea una directory per i log in instance/logs e configura:
1. Un RotatingFileHandler per scrivere log persistenti su file.
2. Un StreamHandler per inviare log alla console.

Entrambi i gestori sono attivi in tutti gli ambienti, ma con livelli 
diversi (DEBUG in sviluppo, INFO in produzione) per adattarsi
sia allo sviluppo locale che al deploy in container.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask


def setup_logging(app: Flask) -> None:
    """
    Configura il logging per l'applicazione Flask.

    Args:
        app: Istanza dell'applicazione Flask.

    Raises:
        RuntimeError: Se la creazione della directory dei log fallisce.
    """

    # Determina l'ambiente e il livello di log
    is_development = app.config.get("FLASK_ENV") == "development"
    log_level = logging.DEBUG if is_development else logging.INFO

    # 1. Definisci un formato di log standard (DRY)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s "
        "[in %(pathname)s:%(lineno)d]",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 2. Configura il RotatingFileHandler (Log su File)
    try:
        log_dir = Path(app.instance_path) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
    except OSError as e:
        logging.error(
            f"Errore nella creazione della directory dei log {log_dir}: {str(e)}"
        )
        raise RuntimeError(f"Impossibile creare la directory dei log: {str(e)}")

    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)

    # 3. Configura il StreamHandler (Log su Console)
    #    MIGLIORAMENTO: Logga sulla console (stdout) anche in produzione,
    #    fondamentale per Gunicorn e Docker (docker-compose logs).
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)

    # 4. Applica i gestori al logger dell'app
    # Rimuove i gestori predefiniti di Flask
    app.logger.handlers = []

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    app.logger.setLevel(log_level)

    # Assicura che i log non vengano passati al logger "root"
    app.logger.propagate = False

    app.logger.info("Logging configurato con successo")
