# app/routes/main/views.py
"""
Route principali dell'applicazione.
Gestione della homepage (dashboard) e pagine statiche.
"""

from flask import current_app, render_template
# --- MODIFICA: Import necessari per la dashboard personale ---
from flask_login import current_user
from sqlalchemy import desc, func
from app.models import Tournament, Player, TournamentPlayer
# --- FINE MODIFICA ---

from . import main_bp as bp
# --- MODIFICA: Import della nuova utility ---
from .utils import get_top_performers, get_player_profit_history
# --- FINE MODIFICA ---
from app import db


@bp.route("/")
def index():
    """
    Homepage: Mostra una dashboard ibrida.
    - Per utenti loggati: Statistiche personali + Panoramica globale.
    - Per visitatori: Pagina di benvenuto.
    """
    current_app.logger.debug("Accesso alla route index ('/').")
    
    # Dati di default
    db_error = False
    error_msg = None
    top_tournaments = []
    top_players = [] # Questo ora conterrà una struttura dati complessa
    personal_tournaments = []
    user_rank = None
    user_stats = None # Conterrà le statistiche chiave dell'utente

    try:
        # Carica i dati solo se l'utente è loggato
        if current_user.is_authenticated:
            
            # --- 1. Dati Globali (Top Tornei) ---
            tournaments_query = db.session.scalars(db.select(Tournament)).all()
            top_tournaments = sorted(
                tournaments_query,
                key=lambda t: t.total_prize_pool or 0,
                reverse=True,
            )[:5]

            # --- 2. Dati per la Classifica (Globale + Personale) ---
            
            # Esegui la query completa per la classifica
            # (Basato sulla logica del tuo utils.py)
            stmt = (
                db.select(Player, func.count(TournamentPlayer.player_id).label("n_tourn"))
                .join(TournamentPlayer, TournamentPlayer.player_id == Player.id, isouter=True)
                .group_by(Player.id)
            )
            rows = db.session.execute(stmt).all()
            all_players_with_stats = [p for (p, _) in rows]
            
            # Ordina l'intera classifica per profitto
            full_leaderboard = sorted(
                all_players_with_stats,
                key=lambda p: p.net_profit or 0,
                reverse=True,
            )

            # Estrai i Top 5 (solo gli oggetti Player per ora)
            top_players_objects = full_leaderboard[:5]
            
            # --- MODIFICA: Carica lo storico per i Top 5 ---
            # Ora `top_players` (passato al template) sarà una lista di dizionari
            top_players = []
            for player_obj in top_players_objects:
                
                # --- MODIFICA: Ora riceviamo (profitti, nomi) ---
                profit_history, tournament_names, tournament_ids = get_player_profit_history(player_obj.id, limit=10)
                
                # Crea le etichette per l'asse X (es. "T1", "T2"...)
                chart_labels = [f"T{i+1}" for i in range(len(profit_history))]
                
                player_data = {
                    "id": player_obj.id,
                    "nickname": player_obj.nickname,
                    "net_profit": player_obj.net_profit,
                    "num_tournaments": player_obj.num_tournaments
                }
                
                top_players.append({
                    "player": player_data, # <- Ora è un dizionario, NON un oggetto Player
                    "profit_history": profit_history,
                    "chart_labels": chart_labels,
                    "tournament_names": tournament_names,
                    "tournament_ids": tournament_ids
                })
            # --- FINE MODIFICA ---


            # Trova la posizione (rank) dell'utente corrente
            user_rank = "N/A"
            for i, player in enumerate(full_leaderboard):
                if player.id == current_user.id:
                    user_rank = i + 1
                    # Prendiamo anche le sue statistiche aggiornate
                    user_stats = player
                    break
            
            # Se l'utente non è in classifica (es. 0 tornei), carica comunque le sue stats
            if not user_stats:
                user_stats = db.session.get(Player, current_user.id)


            # --- 3. Dati Personali (Ultimi tornei dell'utente) ---
            stmt_personal = (
                db.select(TournamentPlayer)
                .join(Tournament)
                .filter(TournamentPlayer.player_id == current_user.id)
                .order_by(desc(Tournament.tournament_date))
                .limit(5)
            )
            personal_tournaments = db.session.scalars(stmt_personal).all()

            if not top_players and not tournaments_query:
                current_app.logger.warning(
                    "Nessun performer trovato (es. nessun torneo giocato)."
                )

    except Exception as e:
        current_app.logger.error(
            f"Errore nel caricare la dashboard: {e}", exc_info=True
        )
        db_error = True
        error_msg = "Impossibile caricare i dati della dashboard."
        # Resetta tutto in caso di errore
        top_tournaments = []
        top_players = []
        personal_tournaments = []
        user_rank = None
        user_stats = None

    if top_players is None:
        top_players = []
        
    return render_template(
        "main/index.html",
        tournaments=top_tournaments,       # Globali
        players=top_players,             # Globali (ora con dati storici)
        personal_tournaments=personal_tournaments, # Personali
        user_rank=user_rank,               # Personale
        user_stats=user_stats,             # Personale
        db_error=db_error,
        error_msg=error_msg,
    )


@bp.route("/about")
def about():
    """Pagina About."""
    current_app.logger.debug("Accesso alla pagina About.")
    return render_template("main/about.html")