# app/routes/players/__init__.py
"""
Blueprint per le route relative alla gestione dei giocatori.
"""
from flask import Blueprint

# Definisce il blueprint
players_bp = Blueprint(
    "players",
    __name__,
    url_prefix="/players",
    template_folder="templates",  # Specifica sottocartella per i template
)

# Importa le viste DOPO la creazione del blueprint per evitare import circolari
from . import views

__all__ = ["players_bp"]
