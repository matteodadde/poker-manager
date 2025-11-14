# app/filters.py

"""
Modulo per registrare filtri Jinja2 personalizzati.
"""


def register_filters(app):
    """
    Registra i filtri Jinja2 custom nell'app.

    Args:
        app (Flask): Istanza dell'app Flask.
    """

    def has_endpoint(endpoint_name: str) -> bool:
        """
        Verifica se un endpoint esiste nella mappa delle view.

        Args:
            endpoint_name (str): Nome dell'endpoint da verificare.

        Returns:
            bool: True se l'endpoint esiste, False altrimenti.
        """
        try:
            return any(
                rule.endpoint == endpoint_name for rule in app.url_map.iter_rules()
            )
        except RuntimeError:
            # Problemi nel runtime (es. app non pronta)
            return False

    app.jinja_env.filters["has_endpoint"] = has_endpoint
    app.jinja_env.globals["has_endpoint"] = has_endpoint
    app.logger.info("Filtro Jinja2 'has_endpoint' registrato con successo")
