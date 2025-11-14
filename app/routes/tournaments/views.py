# app/routes/tournaments/views.py
from flask import render_template, redirect, url_for, flash, current_app, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from sqlalchemy.orm import selectinload, joinedload
from decimal import Decimal
from app.utils.decorators import admin_required
from functools import wraps

from app import db
from app.models import Tournament, Player, TournamentPlayer
from .forms import TournamentForm, DeleteTournamentForm
from . import tournaments_bp as bp

# --- HELPERS ---

def _get_player_choices():
    """Restituisce [(id, nickname), ...] ordinati, più opzione vuota."""
    try:
        players = db.session.scalars(db.select(Player).order_by(Player.nickname)).all()
        choices = [("0", "--- Seleziona Giocatore ---")]
        choices.extend([(str(p.id), p.nickname) for p in players])
        return choices
    except SQLAlchemyError as e:
        current_app.logger.error(
            f"Errore DB nel caricare la lista giocatori per select: {e}"
        )
        return [("0", "--- Errore Caricamento ---")]


def handle_db_error(operation_desc: str, exception: Exception, rollback: bool = True):
    """Logga errore, fa rollback, mostra flash message."""
    current_app.logger.error(
        f"Errore DB durante {operation_desc}: {exception}", exc_info=True
    )
    if rollback:
        db.session.rollback()
    flash(
        f"Si è verificato un errore nel database durante {operation_desc}. Riprova.",
        "danger",
    )


# --- MODIFICA: Nuovo Helper ---
def _populate_participant_choices(form: TournamentForm, choices: list):
    """Popola le 'choices' per tutti i sub-form 'player_id' nel FieldList."""
    for entry_form in form.participants:
        entry_form.player_id.choices = choices


# --- FINE MODIFICA ---


# --- ROTTE ---


@bp.route("/", strict_slashes=False)
@login_required
def list():
    """Mostra la lista di tutti i tornei."""
    try:
        stmt = (
            db.select(Tournament)
            .options(
                joinedload(Tournament.admin),
                selectinload(Tournament.tournament_players),
            )
            .order_by(desc(Tournament.tournament_date))
        )
        tournaments = db.session.scalars(stmt).all()
        current_app.logger.info(f"Lista tornei caricata: {len(tournaments)} trovati.")
        delete_form = DeleteTournamentForm()
        return render_template(
            "tournaments/list.html", tournaments=tournaments, delete_form=delete_form
        )
    except SQLAlchemyError as e:
        handle_db_error("caricamento lista tornei", e, rollback=False)
        return render_template(
            "tournaments/list.html", tournaments=[], delete_form=DeleteTournamentForm()
        )


@bp.route("/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_tournament():
    """Aggiunge un nuovo torneo e i suoi partecipanti."""
    form = TournamentForm()
    player_choices = _get_player_choices()

    # --- MODIFICA: Usa helper ---
    # Popola le scelte per eventuali righe già presenti (es. su POST fallito)
    _populate_participant_choices(form, player_choices)
    # --- FINE MODIFICA ---

    if form.validate_on_submit():
        try:
            new_tournament = Tournament(
                admin_id=current_user.id,
                name=form.name.data.strip(),
                tournament_date=form.tournament_date.data,
                buy_in=form.buy_in.data,
                prize_pool=form.prize_pool.data,
                location=form.location.data.strip() if form.location.data else None,
            )
            db.session.add(new_tournament)
            db.session.flush()  # Ottieni ID

            participants_added = 0

            # --- MODIFICA: Rimossa logica duplicati ---
            # Il validatore `validate_participants` in forms.py
            # gestisce già il controllo dei duplicati prima di arrivare qui.
            # -------------------------------------------

            for entry_form in form.participants:
                if not entry_form.player_id.data:
                    continue

                tp = TournamentPlayer(
                    tournament_id=new_tournament.id,
                    player_id=entry_form.player_id.data,
                    posizione=entry_form.position.data,
                    rebuy=entry_form.rebuy.data,
                    rebuy_total_spent=entry_form.rebuy_total_spent.data
                    or Decimal("0.00"),
                    prize=entry_form.prize.data,
                )
                db.session.add(tp)
                participants_added += 1

            db.session.commit()
            flash(
                f"Torneo '{new_tournament.name}' ({participants_added} partecipanti) creato!",
                "success",
            )
            current_app.logger.info(
                f"Nuovo torneo (ID:{new_tournament.id}) creato da admin {current_user.nickname}."
            )
            return redirect(
                url_for("tournaments.detail", tournament_id=new_tournament.id)
            )

        except SQLAlchemyError as e:
            handle_db_error("salvataggio nuovo torneo", e)
        except Exception as e:
            handle_db_error("processamento dati torneo", e)

    elif request.method == "POST":
        current_app.logger.warning(
            f"Errori validazione form aggiunta torneo: {form.errors}"
        )
        flash("Errore nel form, controlla i campi evidenziati.", "warning")
        # Non è necessario ri-popolare le scelte qui,
        # _populate_participant_choices lo ha già fatto prima del validate.

    return render_template(
        "tournaments/add_edit.html",
        form=form,
        title="Aggiungi Torneo",
        all_players_json=player_choices,  # Passa a JS per nuove righe
    )


@bp.route("/<int:tournament_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_tournament(tournament_id: int):
    """Modifica un torneo esistente e i suoi partecipanti."""
    tournament = db.get_or_404(Tournament, tournament_id)
    player_choices = _get_player_choices()

    if request.method == "GET":
        # --- MODIFICA: Stile Query 2.0 ---
        stmt_tp = (
            db.select(TournamentPlayer)
            .filter_by(tournament_id=tournament_id)
            .order_by(TournamentPlayer.player_id)  # Mantieni ordine
        )
        existing_participants_db = db.session.scalars(stmt_tp).all()
        # --- FINE MODIFICA ---

        existing_participants_data = [
            {
                # --- CORREZIONE: Usa player_id come chiave, non tp.id ---
                "tp_id": tp.player_id,
                "player_id": tp.player_id or None,
                "position": tp.posizione,
                "rebuy": tp.rebuy,
                "rebuy_total_spent": tp.rebuy_total_spent,
                "prize": tp.prize,
            }
            for tp in existing_participants_db
        ]

        form = TournamentForm(obj=tournament)
        for participant_data in existing_participants_data:
            form.participants.append_entry(participant_data)

        # Popola le scelte dopo aver aggiunto le entry
        _populate_participant_choices(form, player_choices)

    else:  # POST
        form = TournamentForm()
        # Popola le scelte per permettere la validazione
        _populate_participant_choices(form, player_choices)

    if form.validate_on_submit():
        try:
            tournament.name = form.name.data.strip()
            tournament.tournament_date = form.tournament_date.data
            tournament.buy_in = form.buy_in.data
            tournament.prize_pool = form.prize_pool.data
            tournament.location = (
                form.location.data.strip() if form.location.data else None
            )

            # --- MODIFICA: Stile Query 2.0 ---
            stmt_current_tp = db.select(TournamentPlayer).filter_by(
                tournament_id=tournament.id
            )
            current_participants_db = db.session.scalars(stmt_current_tp).all()
            # --- FINE MODIFICA ---

            # --- CORREZIONE: Mappa per player_id, non per tp.id ---
            current_tp_map = {str(tp.player_id): tp for tp in current_participants_db}

            # Logica di Sincronizzazione
            player_ids_to_keep = set()
            for entry in form.participants:
                # 'tp_id' ora contiene il player_id vecchio/originale
                original_player_id = entry.tp_id.data
                new_player_id = entry.player_id.data

                if not new_player_id:  # Salta righe vuote
                    continue

                player_ids_to_keep.add(new_player_id)

                if new_player_id in current_tp_map:
                    # 1. Aggiorna Esistenti
                    tp_obj = current_tp_map[new_player_id]
                    tp_obj.posizione = entry.position.data
                    tp_obj.rebuy = entry.rebuy.data or 0
                    tp_obj.rebuy_total_spent = entry.rebuy_total_spent.data or Decimal(
                        "0.00"
                    )
                    tp_obj.prize = entry.prize.data or Decimal("0.00")
                elif new_player_id not in current_tp_map:
                    # 2. Aggiungi Nuovi (il 'tp_id' era vuoto o non trovato)
                    new_tp = TournamentPlayer(
                        tournament_id=tournament.id,
                        player_id=new_player_id,
                        posizione=entry.position.data,
                        rebuy=entry.rebuy.data or 0,
                        rebuy_total_spent=entry.rebuy_total_spent.data
                        or Decimal("0.00"),
                        prize=entry.prize.data or Decimal("0.00"),
                    )
                    db.session.add(new_tp)

            # 3. Elimina Rimossi
            for player_id_str, tp_obj in current_tp_map.items():
                if player_id_str not in player_ids_to_keep:
                    db.session.delete(tp_obj)

            db.session.commit()
            flash(f"Torneo '{tournament.name}' aggiornato!", "success")
            current_app.logger.info(
                f"Torneo (ID:{tournament.id}) aggiornato da admin {current_user.nickname}."
            )
            return redirect(url_for("tournaments.detail", tournament_id=tournament.id))

        except SQLAlchemyError as e:
            handle_db_error(f"salvataggio modifiche torneo (ID:{tournament_id})", e)
        except Exception as e:
            handle_db_error(
                f"processamento dati modifica torneo (ID:{tournament_id})", e
            )

    elif request.method == "POST":
        flash("Errore nel form, controlla i campi evidenziati.", "warning")
        current_app.logger.warning(
            f"Errori validazione form modifica torneo (ID:{tournament_id}): {form.errors}"
        )
        # Le scelte sono già state popolate dall'helper

    return render_template(
        "tournaments/add_edit.html",
        form=form,
        title="Modifica Torneo",
        tournament=tournament,
        all_players_json=player_choices,  # Per JS
    )


@bp.route("/<int:tournament_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_tournament(tournament_id: int):
    """Elimina un torneo."""
    tournament = db.get_or_404(Tournament, tournament_id)
    form = DeleteTournamentForm()
    if form.validate_on_submit():
        try:
            name = tournament.name
            db.session.delete(tournament)
            db.session.commit()
            flash(f"Torneo '{name}' eliminato con successo!", "success")
            current_app.logger.info(
                f"Torneo eliminato da admin {current_user.nickname} (ID: {tournament_id}, Nome: {name})."
            )
            return redirect(url_for("tournaments.list"))
        except SQLAlchemyError as e:
            handle_db_error(f"eliminazione torneo (ID:{tournament_id})", e)
            return redirect(url_for("tournaments.list"))
    else:
        flash("Richiesta di eliminazione non valida o scaduta.", "danger")
        current_app.logger.warning(
            f"Tentativo fallito eliminazione torneo (ID:{tournament_id}) - CSRF invalido."
        )
        return redirect(url_for("tournaments.list"))


@bp.route("/<int:tournament_id>", strict_slashes=False)
@login_required
def detail(tournament_id: int):
    """Mostra i dettagli di un torneo."""
    try:
        stmt = (
            db.select(Tournament)
            .options(
                selectinload(Tournament.tournament_players).joinedload(
                    TournamentPlayer.player
                )
            )
            .filter_by(id=tournament_id)
        )
        tournament = db.session.scalar(stmt)
        if not tournament:
            abort(404)

        # Ordinamento corretto (gestisce None)
        participants = sorted(
            tournament.tournament_players,
            key=lambda p: (
                p.posizione is None,
                p.posizione if p.posizione is not None else float("inf"),
            ),
        )

        current_app.logger.info(
            f"Dettagli torneo '{tournament.name}' (ID: {tournament.id}) visualizzati."
        )
        delete_form = DeleteTournamentForm()
        return render_template(
            "tournaments/detail.html",
            tournament=tournament,
            participants=participants,
            delete_form=delete_form,
        )
    except SQLAlchemyError as e:
        handle_db_error(
            f"caricamento dettagli torneo ID {tournament_id}", e, rollback=False
        )
        return redirect(url_for("tournaments.list"))
