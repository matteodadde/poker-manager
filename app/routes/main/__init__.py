# app/routes/main/__init__.py
"""
Blueprint per le route principali dell'applicazione.

Definisce il blueprint 'main' senza prefisso URL.
"""
from flask import Blueprint

# Definisce il blueprint
main_bp = Blueprint(
    "main",
    __name__,
    template_folder="templates",  # Specifica la sottocartella (sebbene i template siano in app/templates/main)
)

# Importa le viste alla fine per evitare import circolari
# Questo registra le rotte (es. @main_bp.route) definite in views.py
from . import views

__all__ = ["main_bp"]
