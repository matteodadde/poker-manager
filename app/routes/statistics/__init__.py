# app/routes/statistics/__init__.py
"""
Blueprint per le route relative alle statistiche dei giocatori.
"""
from flask import Blueprint

# Definisce il blueprint 'statistics'
statistics_bp = Blueprint(
    "statistics",
    __name__,
    url_prefix="/statistics",
    template_folder="templates",  # Buona prassi specificarlo
)

# Importa le view DOPO aver definito il blueprint
# Questo collega le route definite in views.py (es. @statistics_bp.route)
# al blueprint. # noqa: F401, E402 richiesto da flake8 qui.
from . import views  # noqa: F401, E402
