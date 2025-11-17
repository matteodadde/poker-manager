# app/routes/auth/__init__.py
from flask import Blueprint

# 1. Crea l'istanza del Blueprint
auth_bp = Blueprint("auth", __name__, template_folder="templates")

# 2. Importa le view DOPO aver creato il blueprint.
# L'import esegue views.py, registrando le route decorate con @auth_bp.
from . import views  # noqa: F401, E402
