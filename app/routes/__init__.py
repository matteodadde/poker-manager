# app/routes/__init__.py

"""
Inizializzazione delle route dell'applicazione.

Registra i blueprint per:
- main: homepage e pagina About
- players: gestione dei giocatori
- tournaments: gestione dei tornei
- statistics: statistiche dei giocatori
"""

from app.routes.main.views import bp as main_bp
from app.routes.players import players_bp
from app.routes.tournaments import tournaments_bp
from app.routes.statistics import statistics_bp


def register_blueprint(app, bp, desc, prefix):
    """
    Registra un singolo blueprint sull'app Flask con gestione degli errori.

    Args:
        app (Flask): Istanza Flask.
        bp (Blueprint): Blueprint da registrare.
        desc (str): Descrizione del blueprint.
        prefix (str|None): Prefisso URL per il blueprint.

    Raises:
        RuntimeError: Se la registrazione fallisce.
    """
    try:
        app.register_blueprint(bp, url_prefix=prefix)
        app.logger.info(
            f"Blueprint '{bp.name}' ({desc}) registrato con prefisso {prefix or '/'}"
        )
    except Exception as e:
        app.logger.error(
            f"Errore durante la registrazione di '{bp.name}' ({desc}): {str(e)}"
        )
        raise RuntimeError(f"Impossibile registrare '{bp.name}': {str(e)}")


def init_routes(app):
    """
    Registra tutti i blueprint nell'applicazione Flask con prefissi URL appropriati.

    Args:
        app (Flask): Istanza dell'applicazione Flask.

    Raises:
        RuntimeError: Se la registrazione di un blueprint fallisce.
    """
    blueprints = [
        {"bp": main_bp, "desc": "Main routes", "prefix": None},
        {"bp": players_bp, "desc": "Players routes", "prefix": "/players"},
        {"bp": tournaments_bp, "desc": "Tournaments routes", "prefix": "/tournaments"},
        {"bp": statistics_bp, "desc": "Statistics routes", "prefix": "/statistics"},
    ]

    for item in blueprints:
        register_blueprint(app, item["bp"], item["desc"], item["prefix"])

    # Log dettagliato delle route in ambiente di sviluppo o se debug abilitato
    if app.config.get("FLASK_ENV") == "development" or app.debug:
        app.logger.debug("Route registrate per i blueprint:")
        for item in blueprints:
            bp = item["bp"]
            app.logger.debug(f"Blueprint: {bp.name} ({item['desc']})")
            rules = [
                r
                for r in app.url_map.iter_rules()
                if r.endpoint.startswith(bp.name + ".")
            ]
            if rules:
                for r in rules:
                    methods = ",".join(sorted(r.methods - {"HEAD", "OPTIONS"}))
                    app.logger.debug(f"  [{methods}] {r}")
            else:
                app.logger.debug("  Nessuna rotta registrata")

    app.logger.info("Tutti i blueprint sono stati registrati con successo")
