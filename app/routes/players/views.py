# app/routes/players/views.py

from flask import render_template, redirect, url_for, flash, current_app, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import asc, desc
from functools import wraps
import os
import secrets
from pathlib import Path
from PIL import Image
from werkzeug.utils import secure_filename
from app import db
from app.models import Player, Tournament, TournamentPlayer, Role
from app.utils.decorators import admin_required
from . import players_bp as bp
from .forms import PlayerForm, DeletePlayerForm
from .utils import get_player_stats, country_code_to_emoji


def _save_avatar(form_picture_data, player_id: int) -> str:
    """
    Salva, ridimensiona e ottimizza l'immagine avatar caricata in DUE formati:
    1. Un thumbnail (es. '12.png') per le viste elenco.
    2. Una versione full-size (es. '12_full.png') per lo zoom.

    Args:
        form_picture_data: Il dato del file dal form (es. form.avatar.data).
        player_id (int): L'ID del giocatore, usato come nome file base.

    Returns:
        str: Il nome del file thumbnail salvato (es. '12.png').
        
    Raises:
        IOError: Se si verifica un errore during il salvataggio o 
                 il ridimensionamento dell'immagine.
    """
    THUMB_SIZE = (128, 128)
    FULL_SIZE = (800, 800)
    
    base_filename = str(player_id)
    thumb_fn = f"{base_filename}.png"
    full_fn = f"{base_filename}_full.png"
    
    static_dir = Path(current_app.static_folder)
    save_dir = static_dir / "images" / "players"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    thumb_path = save_dir / thumb_fn
    full_path = save_dir / full_fn

    try:
        img = Image.open(form_picture_data)

        img_full = img.copy()
        img_full.thumbnail(FULL_SIZE)
        img_full.convert('RGBA').save(full_path, format='PNG', optimize=True)

        img_thumb = img.copy()
        img_thumb.thumbnail(THUMB_SIZE)
        img_thumb.convert('RGBA').save(thumb_path, format='PNG', optimize=True)
        
    except (IOError, OSError) as e:
        current_app.logger.error(
            f"Errore during salvataggio/ridimensionamento avatar per player ID {player_id}: {e}", 
            exc_info=True
        )

        raise IOError(f"Errore during l'elaborazione dell'immagine: {e}")


    return thumb_fn


# --- ROTTE ---

@bp.route("/")
@login_required
def list():
    """Mostra l'elenco di tutti i giocatori."""
    current_app.logger.info("Accesso alla lista giocatori.")
    try:
        stmt = db.select(Player).order_by(asc(Player.nickname))
        players = db.session.scalars(stmt).all()
        current_app.logger.debug(f"Trovati {len(players)} giocatori.")
    except SQLAlchemyError as e:
        current_app.logger.error(
            f"Errore DB nel caricamento lista giocatori: {e}", exc_info=True
        )
        flash("Errore nel caricamento della lista dei giocatori.", "danger")
        players = []

    delete_form = DeletePlayerForm()

    return render_template(
        "players/list.html", players=players, delete_form=delete_form, country_code_to_emoji=country_code_to_emoji
    )


@bp.route("/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_player():
    """Aggiunge un nuovo giocatore (solo admin)."""
    form = PlayerForm(original_nickname=None, original_email=None)

    if form.validate_on_submit():
        try:
            new_player = Player(
                first_name=form.first_name.data.strip()
                if form.first_name.data
                else None,
                last_name=form.last_name.data.strip() if form.last_name.data else None,
                nickname=form.nickname.data.strip(),
                email=form.email.data.strip().lower(),
                country=form.country.data or None,
            )
            new_player.password = form.password.data

            user_role = db.session.scalar(db.select(Role).filter_by(name="user"))
            if user_role:
                new_player.roles.append(user_role)
            else:
                current_app.logger.error(
                    "FATAL: Ruolo 'user' non trovato nel DB! Impossibile assegnare ruolo."
                )
                flash("Errore interno: ruolo utente non trovato.", "danger")
                return render_template(
                    "players/add_edit.html", form=form, title="Aggiungi Giocatore"
                )

            db.session.add(new_player)
            db.session.commit() 


            if form.avatar.data:
                try:
                    _save_avatar(form.avatar.data, new_player.id)
                    flash("Avatar caricato con successo!", "info")
                except Exception as e:
                    current_app.logger.error(
                        f"Giocatore creato (ID {new_player.id}) ma caricamento avatar fallito: {e}"
                    )
                    flash(
                        "Giocatore creato, ma si è verificato un errore during il caricamento dell'avatar.",
                        "warning",
                    )

            flash(
                f"Giocatore '{new_player.nickname}' aggiunto con successo!", "success"
            )
            current_app.logger.info(
                f"Nuovo giocatore aggiunto da admin {current_user.nickname} (ID: {new_player.id}, Nick: {new_player.nickname})."
            )
            return redirect(url_for("players.list"))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Errore DB during aggiunta giocatore: {e}", exc_info=True
            )
            flash("Errore during il salvataggio del giocatore.", "danger")
        except ValueError as e:
            db.session.rollback()
            current_app.logger.warning(
                f"Errore di validazione during aggiunta giocatore: {e}"
            )
            flash(f"Errore nei dati inseriti: {e}", "danger")

    if request.method == "POST" and form.errors:
        current_app.logger.warning(
            f"Errori validazione form aggiunta giocatore: {form.errors}"
        )

    return render_template(
        "players/add_edit.html", form=form, title="Aggiungi Giocatore"
    )


@bp.route("/<int:player_id>/edit", methods=["GET", "POST"])
@login_required
# --- MODIFICA: @admin_required RIMOSSO ---
# @admin_required 
def edit_player(player_id: int):
    """
    Modifica un giocatore.
    Accessibile a: Admin (su tutti) O l'utente stesso (solo sul proprio profilo).
    """
    
    # Controlla se l'utente ha un attributo 'is_admin' o un ruolo 'admin'
    # Adatta questo alla tua logica User
    is_admin = getattr(current_user, 'is_admin', False)
    if not is_admin and hasattr(current_user, 'has_role'):
         is_admin = current_user.has_role('admin')

    # Se l'utente NON è admin E l'ID che vuole modificare non è il suo -> 403 Forbidden
    if not is_admin and current_user.id != player_id:
        current_app.logger.warning(f"Accesso NEGATO: Utente {current_user.id} ha tentato di modificare player {player_id}.")
        abort(403) # Assicurati di avere: from flask import abort

    player = db.get_or_404(Player, player_id)

    form = PlayerForm(
        obj=player,
        original_nickname=player.nickname,
        original_email=player.email,
        player_obj=player,
    )

    if form.validate_on_submit():
        try:
            player.first_name = (
                form.first_name.data.strip() if form.first_name.data else None
            )
            player.last_name = (
                form.last_name.data.strip() if form.last_name.data else None
            )
            
            # Esempio: solo un admin può cambiare il nickname
            if is_admin:
                 player.nickname = form.nickname.data.strip()
            elif player.nickname != form.nickname.data.strip():
                 flash("Solo un amministratore può modificare il nickname.", "warning")

            player.email = form.email.data.strip().lower()
            player.country = form.country.data or None

            if form.password.data:
                player.password = form.password.data
                flash("Password aggiornata.", "info")

            # --- LOGICA RIMOZIONE AVATAR ---
            if form.delete_avatar.data:
                try:
                    base_path = Path(current_app.static_folder) / "images" / "players"
                    thumb_path = base_path / f"{player.id}.png"
                    full_path = base_path / f"{player.id}_full.png"
                    
                    if thumb_path.exists():
                        thumb_path.unlink()
                        current_app.logger.info(f"Avatar thumbnail {player.id}.png eliminato.")
                    
                    if full_path.exists():
                        full_path.unlink()
                        current_app.logger.info(f"Avatar full {player.id}_full.png eliminato.")
                        
                    flash("Avatar rimosso con successo.", "info")
                except (IOError, OSError) as e:
                    current_app.logger.error(f"Errore rimozione avatar per player ID {player.id}: {e}", exc_info=True)
                    flash("Si è verificato un errore during la rimozione dell'avatar.", "warning")
            # --- FINE LOGICA RIMOZIONE AVATAR ---

            elif form.avatar.data:
                try:
                    _save_avatar(form.avatar.data, player.id)
                    flash("Avatar aggiornato con successo!", "info")
                except Exception as e:
                    current_app.logger.error(
                        f"Giocatore aggiornato (ID {player.id}) ma caricamento avatar fallito: {e}"
                    )
                    flash(
                        "Dati aggiornati, ma si è verificato un errore during il caricamento dell'avatar.",
                        "warning",
                    )

            db.session.commit()
            
            # --- MODIFICA: Messaggio flash personalizzato ---
            if current_user.id == player.id:
                 flash("Il tuo profilo è stato aggiornato con successo!", "success")
            else:
                flash(f"Giocatore '{player.nickname}' aggiornato con successo!", "success")
            # --- FINE MODIFICA ---
                
            current_app.logger.info(
                f"Giocatore aggiornato da {current_user.nickname} (ID: {player.id}, Nick: {player.nickname})."
            )
            return redirect(url_for("players.detail", player_id=player.id))

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Errore DB during modifica giocatore (ID: {player_id}): {e}",
                exc_info=True,
            )
            flash("Errore durante l'aggiornamento del giocatore.", "danger")
        except ValueError as e:
            db.session.rollback()
            current_app.logger.warning(
                f"Errore di validazione during modifica giocatore (ID: {player_id}): {e}"
            )
            flash(f"Errore nei dati inseriti: {e}", "danger")

    if request.method == "POST" and form.errors:
        current_app.logger.warning(
            f"Errori validazione form modifica giocatore (ID: {player_id}): {form.errors}"
        )

    if request.method == "GET":
        form.process(obj=player)
        form.password.data = ""
        form.confirm_password.data = ""
        form.old_password.data = ""

    # --- MODIFICA: Titolo dinamico ---
    page_title = "Modifica il tuo Profilo" if current_user.id == player_id else f"Modifica Giocatore"
    if not player:
        page_title = "Aggiungi Giocatore" # Fallback per /add
    # --- FINE MODIFICA ---

    return render_template(
        "players/add_edit.html", form=form, title=page_title, player=player
    )


@bp.route("/<int:player_id>/delete", methods=["POST"])
@login_required
@admin_required # <-- MANTENUTO: Solo admin possono eliminare
def delete_player(player_id: int):
    """Elimina un giocatore (solo admin)."""
    player = db.get_or_404(Player, player_id)
    form = DeletePlayerForm()

    if form.validate_on_submit():
        try:
            nickname = player.nickname

            stmt_tp = (
                db.select(TournamentPlayer.player_id)
                .filter_by(player_id=player.id)
                .limit(1)
            )

            if db.session.scalar(stmt_tp):
                flash(
                    f"Impossibile eliminare '{nickname}'. Il giocatore ha partecipazioni ai tornei.",
                    "warning",
                )
                current_app.logger.warning(
                    f"Tentativo fallito da admin {current_user.nickname} di eliminare giocatore (ID: {player_id}) con partecipazioni."
                )
                return redirect(url_for("players.detail", player_id=player_id))
            
            try:
                base_path = Path(current_app.static_folder) / "images" / "players"
                thumb_path = base_path / f"{player.id}.png"
                full_path = base_path / f"{player.id}_full.png"
                
                if thumb_path.is_file():
                    thumb_path.unlink()
                    current_app.logger.info(f"Avatar thumbnail {player.id}.png eliminato.")
                
                if full_path.is_file():
                    full_path.unlink()
                    current_app.logger.info(f"Avatar full {player.id}_full.png eliminato.")
                    
            except Exception as e:
                current_app.logger.error(f"Errore eliminazione avatar per player ID {player.id}: {e}")

            db.session.delete(player)
            db.session.commit()
            flash(f"Giocatore '{nickname}' eliminato con successo!", "success")
            current_app.logger.info(
                f"Giocatore eliminato da admin {current_user.nickname} (ID: {player_id}, Nick: {nickname})."
            )
            return redirect(url_for("players.list"))

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Errore DB during eliminazione giocatore (ID: {player_id}): {e}",
                exc_info=True,
            )
            flash("Errore durante l'eliminazione del giocatore.", "danger")
            return redirect(url_for("players.list"))
    else:
        flash("Richiesta di eliminazione non valida o scaduta.", "danger")
        current_app.logger.warning(
            f"Tentativo fallito da admin {current_user.nickname} di eliminare giocatore (ID: {player_id}) - Token CSRF non valido."
        )
        return redirect(url_for("players.list"))


@bp.route("/<int:player_id>")
@login_required
def detail(player_id: int):
    """Visualizza dettagli e statistiche di un giocatore."""
    try:
        player = db.get_or_404(Player, player_id)
        stats = get_player_stats(player)

        stmt_tournaments = (
            db.select(TournamentPlayer)
            .join(Tournament)
            .filter(TournamentPlayer.player_id == player.id)
            .order_by(desc(Tournament.tournament_date))
        )
        tournaments_played = db.session.scalars(stmt_tournaments).all()

        current_app.logger.info(
            f"Dettagli giocatore '{player.nickname}' (ID: {player.id}) visualizzati."
        )

        delete_form = DeletePlayerForm()

        return render_template(
            "players/detail.html",
            player=player,
            stats=stats,
            tournaments_played=tournaments_played,
            delete_form=delete_form,
        )

    except SQLAlchemyError as e:
        current_app.logger.error(
            f"Errore DB caricamento dettagli giocatore (ID: {player_id}): {e}",
            exc_info=True,
        )
        flash("Errore nel caricamento dei dettagli del giocatore.", "danger")
        return redirect(url_for("players.list"))