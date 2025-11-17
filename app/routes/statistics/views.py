# app/routes/statistics/views.py
"""
Route per le statistiche dei giocatori (Leaderboard).
"""

from flask import render_template, current_app, flash
from flask_login import login_required  # <-- Aggiunto login_required
from sqlalchemy.exc import SQLAlchemyError

from . import statistics_bp as bp  # Usa alias 'bp'
from .utils import get_leaderboard_stats


@bp.route("/leaderboard", strict_slashes=False)
@login_required  # <-- Proteggi la route
def leaderboard():
    """Mostra la leaderboard dei giocatori con statistiche."""
    template_path = "statistics/leaderboard.html"
    stats = []  # Inizializza a lista vuota
    error_message = None  # Inizializza a None

    try:
        stats = get_leaderboard_stats()
        current_app.logger.info(
            f"Accesso alla leaderboard: {len(stats)} giocatori trovati con statistiche."
        )
        if not stats:
            # Usa un messaggio informativo se non ci sono dati, non un errore
            flash("Nessun dato disponibile per la leaderboard al momento.", "info")

    except SQLAlchemyError as e:
        error_message = "Errore nel caricamento della leaderboard. Riprova più tardi."
        current_app.logger.error(
            f"Errore DB durante recupero dati leaderboard: {e}", exc_info=True
        )
        flash(error_message, "danger")  # Mostra flash anche in caso di errore DB

    except Exception as e:
        error_message = (
            "Si è verificato un errore imprevisto durante il calcolo della leaderboard."
        )
        current_app.logger.error(f"Errore imprevisto leaderboard: {e}", exc_info=True)
        flash(error_message, "danger")  # Mostra flash anche per errori generici

    # Passa sempre stats (che può essere vuota) e error_message (che può essere None)
    return render_template(template_path, stats=stats, error_message=error_message)
