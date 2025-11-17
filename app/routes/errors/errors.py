# app/routes/errors/errors.py

"""
Modulo per la gestione centralizzata degli errori HTTP e delle eccezioni.

Registra error handlers globali per 401, 403, 404, 500, errori database,
e errori generici imprevisti.
"""

from flask import (
    render_template,
    request,
    jsonify,
    current_app,
    flash,
    redirect,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

# Importa l'istanza db per il rollback della sessione
from app import db


def register_error_handlers(app):
    """
    Registra i gestori di errore globali sull'app Flask.
    """

    def wants_json_response():
        """Controlla se il client preferisce una risposta JSON."""
        return (
            request.accept_mimetypes.accept_json
            and not request.accept_mimetypes.accept_html
        )

    @app.errorhandler(401)
    def unauthorized_error(e):
        """
        Gestisce l'errore 401 (Unauthorized).
        Reindirizza alla pagina di login, che è l'azione attesa.
        """
        current_app.logger.info(
            f"401 Unauthorized: {request.method} {request.url} - IP: {request.remote_addr}"
        )
        flash("Devi effettuare l'accesso per visualizzare questa pagina.", "info")
        # Passa l'URL corrente come 'next' per reindirizzare l'utente dopo il login
        return redirect(url_for("auth.login", next=request.url))

    @app.errorhandler(403)
    def forbidden_error(e):
        """Gestisce l'errore 403 (Forbidden)."""
        current_app.logger.warning(
            f"403 Forbidden: {request.method} {request.url} - IP: {request.remote_addr} - UA: {request.user_agent.string}"
        )
        if wants_json_response():
            return (
                jsonify(
                    error="Forbidden", message="Non hai i permessi per questa risorsa."
                ),
                403,
            )
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        """Gestisce l'errore 404 (Not Found)."""
        # Loggato come 'info' per ridurre il rumore in produzione
        current_app.logger.info(
            f"404 Not Found: {request.method} {request.url} - IP: {request.remote_addr} - UA: {request.user_agent.string}"
        )
        if wants_json_response():
            return (
                jsonify(
                    error="Not Found",
                    message="La risorsa richiesta non è stata trovata.",
                ),
                404,
            )
        try:
            return render_template("errors/404.html"), 404
        except Exception as render_exc:
            current_app.logger.critical(
                f"Errore nel render della pagina 404: {str(render_exc)}"
            )
            return "Pagina Non Trovata", 404

    @app.errorhandler(400)
    def bad_request_error(e):
        """Gestisce l'errore 400 (Bad Request)."""
        current_app.logger.warning(
            f"400 Bad Request: {request.method} {request.url} - IP: {request.remote_addr} - UA: {request.user_agent.string}"
        )
        if wants_json_response():
            return jsonify(error="Bad Request", message=str(e)), 400
        return render_template("errors/400.html"), 400

    @app.errorhandler(500)
    def internal_server_error(e):
        """Gestisce l'errore 500 (Internal Server Error)."""
        # CRITICO: Esegui il rollback della sessione prima di fare qualsiasi cosa
        try:
            db.session.rollback()
        except Exception as rollback_exc:
            current_app.logger.critical(
                f"Errore durante il rollback della sessione dopo un errore 500: {rollback_exc}"
            )

        current_app.logger.error(
            f"500 Internal Server Error: {str(e)} - URL: {request.url} - IP: {request.remote_addr}",
            exc_info=True,  # Aggiunge il traceback al log
        )
        if wants_json_response():
            return jsonify(error="Internal Server Error"), 500
        try:
            return render_template("errors/500.html"), 500
        except Exception as render_exc:
            current_app.logger.critical(
                f"Errore nel render della pagina 500: {str(render_exc)}"
            )
            return "Errore Interno del Server", 500

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        """Gestisce specificamente gli errori del database."""
        # CRITICO: Esegui il rollback per pulire la sessione
        try:
            db.session.rollback()
        except Exception as rollback_exc:
            current_app.logger.critical(
                f"Errore durante il rollback della sessione dopo un errore DB: {rollback_exc}"
            )

        current_app.logger.error(f"Errore SQLAlchemy: {error}", exc_info=True)
        flash("Si è verificato un errore nel database. Riprova più tardi.", "danger")

        if wants_json_response():
            return jsonify(error="Database Error"), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Gestore "catch-all" per qualsiasi altra eccezione."""

        # Se è un errore HTTP (es. 404, 403) lascialo ai gestori specifici
        if isinstance(error, HTTPException):
            return error

        # CRITICO: Esegui il rollback per tutti gli altri errori
        try:
            db.session.rollback()
        except Exception as rollback_exc:
            current_app.logger.critical(
                f"Errore durante il rollback della sessione dopo un errore imprevisto: {rollback_exc}"
            )

        current_app.logger.error(
            f"Errore imprevisto non gestito: {error}", exc_info=True
        )
        flash("Si è verificato un errore imprevisto.", "danger")

        if wants_json_response():
            return jsonify(error="Unexpected Error"), 500
        return render_template("errors/500.html"), 500
