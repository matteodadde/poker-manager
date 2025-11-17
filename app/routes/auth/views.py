# app/routes/auth/views.py
"""
Blueprint for authentication routes (login, logout).
"""

# --- Import Librerie Standard ---
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone
import logging

# --- Import Terze Parti ---
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError, OperationalError

# --- Import Locali dell'App ---
from app import db, limiter
from app.models.player import Player
from . import auth_bp
from .forms import LoginForm

# Importa l'helper corretto da utils
from app.routes.main.utils import is_safe_url

# Logger
log = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    """Handles user (Player) login using LoginForm."""
    if current_user.is_authenticated:
        flash("Sei già autenticato.", "info")
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        remember = form.remember.data
        log.debug(f"Login attempt for email: {email}")

        try:
            player_stmt = db.select(Player).filter(func.lower(Player.email) == email)
            player = db.session.scalar(player_stmt)

            if player and player.check_password(password):
                # Logica 'is_active' rimossa come richiesto

                login_user(player, remember=remember)

                # --- CORREZIONE BUG AUDIT ---
                # L'audit (aggiornamento DB) è separato dal login.
                # Se questo blocco fallisce, l'utente è comunque loggato.
                try:
                    player.last_login_at = datetime.now(timezone.utc)
                    player.last_login_ip = request.remote_addr
                    db.session.commit()
                except (IntegrityError, OperationalError) as e:
                    log.error(
                        f"Failed to update last_login info for {player.email}: {e}"
                    )
                    db.session.rollback()
                # --- FINE CORREZIONE ---

                log.info(f"Login successful for user: {player.email} (ID: {player.id})")
                flash(f"Bentornato, {player.nickname}!", "success")

                # --- CORREZIONE BUG REDIRECT ---
                next_page = request.args.get("next")
                if next_page and is_safe_url(next_page):
                    log.debug(f"Redirecting logged in user to 'next' page: {next_page}")
                    return redirect(next_page)

                if next_page:  # Se 'next' esiste ma non è sicuro
                    log.warning(
                        f"Unsafe 'next' URL detected: {next_page}. Redirecting to index."
                    )

                log.debug("Redirecting logged in user to index.")
                return redirect(url_for("main.index"))
                # --- FINE CORREZIONE ---

            else:
                # --- CORREZIONE BUG CREDENZIALI ERRATE ---
                log.warning(
                    f"Login failed: Invalid credentials for email attempt: {email}"
                )
                flash("Login non riuscito. Controlla email e password.", "danger")
                # Ritorna 401 e ricarica la pagina di login
                return (
                    render_template("auth/login.html", title="Accedi", form=form),
                    401,
                )
                # --- FINE CORREZIONE ---

        except Exception as e:
            # --- CORREZIONE BUG ECCEZIONE ---
            log.error(
                f"Unexpected error during login for email attempt {email}: {e}",
                exc_info=True,
            )
            db.session.rollback()
            flash(
                "Si è verificato un errore durante il login. Riprova più tardi.",
                "danger",
            )
            # Ritorna 500 e ricarica la pagina di login
            return render_template("auth/login.html", title="Accedi", form=form), 500
            # --- FINE CORREZIONE ---

    # Metodo GET (o validazione form fallita)
    return render_template("auth/login.html", title="Accedi", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """Logs the current user out."""
    user_email = current_user.email
    logout_user()
    log.info(f"User logged out: {user_email}")
    flash("Sei stato disconnesso con successo.", "info")
    return redirect(url_for("main.index"))


# --- Funzione is_safe_url locale RIMOSSA ---
# (Ora usa correttamente quella importata da app.routes.main.utils)
