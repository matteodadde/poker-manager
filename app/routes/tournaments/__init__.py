# app/routes/tournaments/__init__.py
"""
Blueprint for tournament management routes.
"""
from flask import Blueprint

# Define the blueprint with URL prefix
tournaments_bp = Blueprint(
    "tournaments",
    __name__,
    template_folder="templates",
    url_prefix="/tournaments",  # Added prefix here
)

# Import views AFTER defining the blueprint to register routes
# noqa: F401, E402 needed here for flake8
from . import views
