# app/models/__init__.py
"""
Package principale dei modelli dell'applicazione.

Esporta le classi dei modelli principali per un facile accesso.

IMPORTANTE: L'ordine di importazione è cruciale per le dipendenze
di SQLAlchemy (es. Foreign Keys).
"""

# 1. Importa Player (non ha dipendenze o è la dipendenza base)
#    (Viene da app/models/player/__init__.py, che importa da .base)
from .player import Player

# 2. Importa Role (dipende da Player)
#    (Assicurati che esista app/models/roles.py)
from .roles import Role

# 3. Importa gli altri modelli
from .tournament import Tournament
from .tournament_player import TournamentPlayer

# Definisce l'API pubblica di questo package
__all__ = [
    "Player",
    "Role",
    "Tournament",
    "TournamentPlayer",
]
