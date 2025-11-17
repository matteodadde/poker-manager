# commands.py
"""
Defines custom Flask CLI commands for the application.
Includes commands for creating users/admins with a password (no activation).
"""
import os
import sys
import logging
import click
from dotenv import load_dotenv

# --- Load Environment Variables ---
# Carica il .env SOLO se non siamo in un ambiente (come Docker)
# che ha già impostato le variabili per noi.
if not os.getenv("DATABASE_URL"):
    try:
        if load_dotenv():
            print("commands.py: Variabili d'ambiente caricate da .env (modalità locale)")
        else:
            print("commands.py: .env non trovato.")
    except Exception as e:
        print(f"commands.py: Errore caricamento .env: {e}")

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
log = logging.getLogger(__name__)

# --- Import
try:
    from app_factory import create_app
    from app import db as app_db
    from app.models.player import Player
    from app.models.roles import Role, create_default_roles
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError
except ImportError: # pragma: no cover
    log.critical(
        "FATAL ERROR: Could not import app_factory or models. Ensure it's in the project root."
    )
    sys.exit(1)


# --- Variabili globali per app e db ---
# Verranno popolate o dalla creazione (produzione) o dai test (testing)
app = None
db = None
logger = log

def register_commands(app_to_register):
    """
    Registra tutti i comandi CLI sull'istanza dell'app fornita.
    """
    global db, logger
    
    db = app_to_register.extensions['sqlalchemy']
    logger = app_to_register.logger
    
    @app_to_register.cli.command("init-roles")
    def init_roles_command():
        """Creates the default 'admin' and 'user' roles if they don't exist."""
        logger.info("Executing 'flask init-roles' command...")
        with app_to_register.app_context():
            try:
                created_roles = create_default_roles()
                if created_roles:
                    click.echo(f"Successfully created roles: {', '.join(created_roles)}") # pragma: no cover
                else:
                    click.echo("Default roles 'admin' and 'user' already exist.")
                logger.info("'init-roles' command finished successfully.")
            except Exception as e:
                # La linea 64 (sotto) è coperta dal test test_init_roles_exception
                # A volte il coverage può avere problemi con i logger, ma il test è corretto.
                logger.error(f"Error during 'init-roles': {e}", exc_info=True)
                click.echo(f"ERROR during role initialization: {e}", err=True)

    @app_to_register.cli.command("create-admin")
    @click.option("--nickname", required=True)
    @click.option("--email", required=True)
    @click.option("--password", required=True, hide_input=True)
    @click.option("--first-name", default="Admin")
    @click.option("--last-name", default="Admin")
    @click.option("--country", default=None)
    def create_admin_command(nickname, email, password, first_name, last_name, country):
        """Creates a new admin user, sets password, and activates immediately."""
        logger.info(f"Executing 'flask create-admin' for nickname: {nickname}")
        _create_or_update_player(
            app_to_register, nickname, email, first_name, last_name, country, password, is_admin=True
        )

    @app_to_register.cli.command("create-user")
    @click.option("--nickname", required=True)
    @click.option("--email", required=True)
    @click.option("--password", required=True, hide_input=True)
    @click.option("--first-name", required=True)
    @click.option("--last-name", required=True)
    @click.option("--country", default=None)
    def create_user_command(nickname, email, password, first_name, last_name, country):
        """Creates a new standard user, sets password, and activates immediately."""
        logger.info(f"Executing 'flask create-user' for nickname: {nickname}")
        _create_or_update_player(
            app_to_register, nickname, email, first_name, last_name, country, password, is_admin=False
        )

    @app_to_register.cli.command("list-users")
    @click.option("--role", default=None, help="Filter by role name (e.g., admin).")
    def list_users_command(role):
        """Lists users, optionally filtering by role."""
        logger.info(f"Executing 'flask list-users' (filter: {role})")
        with app_to_register.app_context():
            try:
                query = db.select(Player).order_by(Player.nickname)
                if role:
                    query = query.join(Player.roles).filter(Role.name.ilike(role))

                users = db.session.scalars(query).all()

                if not users:
                    click.echo(f"No users found{f' with role {role}' if role else ''}.")
                    return

                click.echo(f"--- Users{f' (Role: {role})' if role else ''} ---")
                for user in users:
                    roles = ", ".join(r.name for r in user.roles)
                    activated = "Yes (Password Set)" if user.password_hash else "No (Password NOT Set)"
                    
                    click.echo(
                        f"ID: {user.id:<4} Nick: {user.nickname:<15} Email: {user.email:<25} "
                        f"Roles: [{roles}] Activated: {activated}"
                    )
                click.echo(f"--- Total: {len(users)} ---")

            except Exception as e:
                logger.error(f"Error listing users: {e}", exc_info=True)
                click.echo(f"ERROR listing users: {e}", err=True)


# --- Helper function per la creazione del giocatore ---
def _create_or_update_player(
    app_instance, nickname, email, first_name, last_name, country, password, is_admin
):
    """Helper function to create a player, set password, and activate."""
    with app_instance.app_context():
        try:
            # --- Validazione Input ---
            if not nickname or len(nickname) < 3:
                click.echo("Error: Nickname is required (min 3 chars).", err=True)
                return
            if not email or "@" not in email:
                click.echo("Error: Valid email is required.", err=True)
                return
            if not password or len(password) < 8:
                click.echo("Error: Password is required (min 8 chars).", err=True)
                return
            if country and len(country) != 2:
                click.echo("Error: Country code must be 2 letters.", err=True)
                return

            # --- Trova Ruolo ---
            role_name = "admin" if is_admin else "user"
            target_role = db.session.scalar(db.select(Role).filter_by(name=role_name))
            if not target_role:
                click.echo(
                    f"Error: '{role_name}' role not found. Run 'flask init-roles' first.",
                    err=True,
                )
                return

            # --- Controlla Esistenza ---
            existing_player = db.session.scalar(
                db.select(Player).filter(
                    (Player.nickname.ilike(nickname))
                    | (Player.email.ilike(email))
                )
            )
            if existing_player:
                click.echo(
                    f"Error: Player with nickname '{nickname}' or email '{email}' already exists.",
                    err=True,
                )
                return

            # --- Crea Giocatore ---
            player = Player(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                nickname=nickname.strip(),
                email=email.lower().strip(),
                country=country.upper().strip() if country else None,
            )
            
            player.password = password.strip() # Imposta e hash della password
            player.roles.append(target_role)

            db.session.add(player)
            db.session.commit()

            role_display = "ADMIN" if is_admin else "USER"
            click.echo(
                f"✅ {role_display} player '{nickname}' (ID {player.id}) created and activated successfully."
            )
            logger.info(f"{role_display} player '{nickname}' created and activated.")

        except ValueError as ve:
            db.session.rollback()
            logger.warning(f"Validation error creating player {nickname}: {ve}", exc_info=False)
            click.echo(f"Validation Error: {ve}", err=True)
        except IntegrityError:
            db.session.rollback()
            logger.warning(f"Integrity error creating player {nickname} (likely duplicate).")
            click.echo(
                f"Error: Player with nickname '{nickname}' or email '{email}' likely already exists.",
                err=True,
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating player {nickname}: {e}", exc_info=True)
            click.echo(f"ERROR creating player: {e}", err=True)


# --- Creazione App e Registrazione Comandi (per produzione) ---
if not os.environ.get("PYTEST_RUNNING"): # pragma: no cover
    try:
        app = create_app(is_testing=False)
        logger = app.logger if hasattr(app, "logger") else log
        
        # Registra i comandi sull'app di produzione
        register_commands(app)
        
        logger.info("commands.py: Flask app instance created and commands registered for CLI.")
    except Exception as e:
        log.critical(f"FATAL ERROR during Flask app creation for CLI: {e}", exc_info=True)
        sys.exit(1)