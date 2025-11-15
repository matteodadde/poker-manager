# app_factory.py
"""
Factory function to create and configure the Flask application instance.

This module centralizes the creation of the Flask app, ensuring all
configurations, extensions, blueprints, and necessary hooks are set up
correctly following the application factory pattern.
"""

import logging
from pathlib import Path

# Import 'request' and 'current_app' along with 'Flask'
from flask import (
    Flask,
    current_app,
    request,
    url_for,
)  # <-- Added url_for import for helper
from datetime import datetime

# --- 1. Import Configuration (MUST BE FIRST) ---
# Import the pre-configured 'config' instance and the canonical 'BASE_DIR'.
# This triggers the .env loading, environment selection logic, and initial
# validation checks in app/config/__init__.py
try:
    # This import statement runs app/config/__init__.py
    from app.config import config
    from app.config.base import BASE_DIR
except (
    ImportError,
    ValueError,
    RuntimeError,
) as e:  # Catch errors from config loading/validation
    # Use basicConfig for logging before app logger is ready
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(
        f"FATAL: Application startup failed during configuration import/validation: {e}",
        exc_info=False,
    )  # Keep traceback minimal here
    # Re-raise as RuntimeError to ensure app doesn't start
    raise RuntimeError(f"Configuration failed: {e}")


# --- 2. Import Extensions (from app/__init__.py) ---
# Import the *empty* extension instances created in app/__init__.py
try:
    from app import db, migrate, bcrypt, login_manager, csrf, limiter # <-- AGGIUNTO limiter

    # Import other extensions if you added them to app/__init__.py
    # from app import mail
except ImportError as e:
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(
        f"FATAL: Could not import extensions from 'app/__init__.py': {e}. "
        "Ensure the file exists and instances are defined.",
        exc_info=True,
    )
    raise RuntimeError(f"Failed to import extensions from app: {e}")

# --- 3. Import App Modules & Models ---
# Import registration functions and necessary models AFTER config and extensions
try:
    # Ensure logging_config.py is in the project root or adjust path
    from app.logging_config import setup_logging
    from app.routes import init_routes
    from app.routes.errors.errors import register_error_handlers
    from app.utils.filters import register_filters
    from app.utils.decimal import round_decimal
except ImportError as e:
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(
        f"FATAL: Failed to import core app modules (logging_config, routes, errors, filters): {e}",
        exc_info=True,
    )
    raise RuntimeError(f"Failed to import core app modules: {e}")


# --- CRITICAL BLOCK: Import ALL Models ---
# Import all SQLAlchemy models here AFTER 'db' instance is imported.
# This ensures they are registered with the correct 'db' instance metadata
# before any operations (like db.create_all or Flask-Migrate).
# The order is crucial if models have dependencies (e.g., Foreign Keys).
try:
    # 1. Import Player (base model, often used for login)
    from app.models.player.base import Player

    # 2. Import Role (depends on Player for the relationship)
    from app.models.roles import Role

    # 3. Import other models
    from app.models.tournament.base import Tournament
    from app.models.tournament_player.base import TournamentPlayer

    # Add any other models here... e.g., from app.models.some_other_model import SomeOtherModel
    # Use basic print as logger might not be fully configured yet
    print("INFO: Successfully imported all SQLAlchemy models.")
except ImportError:
    # Use basicConfig as app logger might not be ready
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(
        "FATAL: One or more models failed to import (Player, Role, Tournament, TournamentPlayer?). Check paths and dependencies.",
        exc_info=True,
    )
    raise RuntimeError("Model import failed. Check logs for details.")
# --- END CRITICAL BLOCK ---

# Get a logger instance for the factory itself
# Use __name__ which will resolve to 'app_factory'
log = logging.getLogger(__name__)


def create_app(is_testing: bool = False) -> Flask:
    """
    Creates, organizes, and returns a Flask application instance.

    Uses the imported 'config' object (determined by FLASK_ENV) by default,
    but allows overriding with 'is_testing=True' for test environments.

    Args:
        is_testing (bool): If True, forces loading of TestingConfig.

    Returns:
        Flask: The configured Flask application instance.
    """
    log.info(f"Application factory called. is_testing={is_testing}")

    # --- Paths (Based on BASE_DIR from app.config.base) ---
    template_path = BASE_DIR / "app" / "templates"
    static_path = BASE_DIR / "app" / "static"
    instance_path = BASE_DIR / "instance"

    # --- Ensure Instance Folder Exists ---
    try:
        instance_path.mkdir(exist_ok=True)
        log.debug(f"Instance folder checked/created: {instance_path}")
    except OSError as e:
        log.critical(
            f"FATAL: Could not create/access instance folder '{instance_path}': {e}",
            exc_info=True,
        )
        raise RuntimeError(f"Failed to create/access instance folder: {e}")

    # --- Create Flask Instance ---
    # Use 'app' which is the actual package name for consistency
    app = Flask(
        "app",  # Use the package name 'app'
        instance_path=str(instance_path),
        template_folder=str(template_path),
        static_folder=str(static_path),
        instance_relative_config=True,  # Allows loading e.g., config.py from instance folder
    )
    log.info(f"Flask app instance created: {app.name}")

    # --- 1. Load Configuration ---
    config_object_to_load = None
    if is_testing:
        log.info(
            "is_testing=True flag detected. Attempting to load and instantiate TestingConfig."
        )
        try:
            from app.config.testing import TestingConfig

            config_object_to_load = TestingConfig()
        except ImportError:
            log.critical(
                "FATAL: TestingConfig not found in app.config.testing.", exc_info=True
            )
            raise RuntimeError("TestingConfig class not found.")
        except Exception as e:
            log.critical(
                f"FATAL: Error instantiating TestingConfig: {e}", exc_info=True
            )
            raise RuntimeError(f"Failed to instantiate TestingConfig: {e}")
    else:
        # Use the pre-imported and validated config instance from app/config/__init__.py
        config_object_to_load = config  # Use the instance directly
        log.info(
            f"Using pre-loaded config object from app.config: {config.__class__.__name__}"
        )

    try:
        # Apply the chosen configuration object to the Flask app instance
        app.config.from_object(config_object_to_load)
        log.info(
            f"Applied configuration from {config_object_to_load.__class__.__name__} to Flask app."
        )

        # Ensure BASE_DIR is explicitly available in app.config if needed later
        # (it might not be explicitly set in all Config classes)
        if "BASE_DIR" not in app.config:
            app.config["BASE_DIR"] = BASE_DIR

    except Exception as e:
        config_name = (
            config_object_to_load.__class__.__name__
            if config_object_to_load
            else "selected config object"
        )
        log.critical(
            f"FATAL: Failed to load configuration from object {config_name}: {e}",
            exc_info=True,
        )
        raise RuntimeError(f"Failed to load configuration object: {e}")

    # --- 2. Configure Logging (NOW, after config is loaded) ---
    try:
        # setup_logging should use app.config['LOG_LEVEL'], etc.
        setup_logging(app)
        # Verify logger is working
        app.logger.info(
            f"Application logging configured successfully for environment: {app.config.get('ENV', 'unknown').upper()}"
        )
        app.logger.info(
            f"Effective Log Level set to: {logging.getLevelName(app.logger.getEffectiveLevel())}"
        )
    except Exception as e:
        # Fallback to basicConfig, log error
        logging.basicConfig(level=logging.ERROR)
        logging.error(
            f"CRITICAL ERROR during application logging configuration: {e}",
            exc_info=True,
        )
        # Ensure app.logger exists even if basic
        if not hasattr(app, "logger") or not isinstance(app.logger, logging.Logger):
            # Use the correct app name here
            app.logger = logging.getLogger(app.name)
        app.logger.error(
            "!!! Application logging setup failed, using basic configuration !!!"
        )

    # --- 3. Set Global Template Variables ---
    @app.context_processor
    def inject_global_vars():
        # Variables returned here are available in all Jinja2 templates
        return {
            "current_year": datetime.now().year,
            "APP_NAME": app.config.get(
                "APP_NAME", "Poker App"
            ),  # Example: Make app name global
        }

    app.logger.debug(
        "Global Jinja context processor registered (current_year, APP_NAME)."
    )

    # --- 4. Verify Essential Configurations (Log values) ---
    app.logger.debug(f"Current Environment: {app.config.get('ENV', 'unknown').upper()}")
    app.logger.debug(f"Debug Mode Active: {app.debug}")
    app.logger.debug(f"Testing Mode Active: {app.testing}")
    # Log DB URI carefully
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if app.debug or app.testing:
        # In debug/test, log the full URI for easier debugging
        app.logger.debug(f"Database URI Used: {db_uri}")
    else:
        # In production, just confirm it's set without revealing sensitive details
        db_uri_log = (
            "Set (details hidden in production)"
            if db_uri
            else "!!! NOT SET !!! (Validation should have caught this)"
        )
        app.logger.info(f"Database URI Status: {db_uri_log}")
    # SECRET_KEY validation happened earlier, confirm loaded status
    app.logger.info(
        f"Secret Key Loaded: {'Yes' if app.config.get('SECRET_KEY') else 'NO - FATAL ERROR'}"
    )
    app.logger.info(
        f"CSRF Protection Enabled: {app.config.get('WTF_CSRF_ENABLED', 'Not Set (Check BaseConfig)')}"
    )

    # --- 5. Initialize Extensions with the App ---
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        bcrypt.init_app(app)
        login_manager.init_app(app)
        csrf.init_app(app)
        limiter.init_app(app) # <-- AGGIUNTO init_app per limiter
        
        # Initialize other extensions here: mail.init_app(app)
        
        app.logger.info("Flask-WTF CSRF protection initialized with app instance.")
        app.logger.info(
            "Core extensions (db, migrate, bcrypt, login_manager, limiter, csrf) initialized with app instance."
        )
    except Exception as e:
        app.logger.critical(
            f"FATAL: Error during core extension initialization: {e}", exc_info=True
        )
        raise RuntimeError(f"Failed to initialize core extensions: {e}")

    # --- 6. Configure Flask-Login ---
    @login_manager.user_loader
    def load_user(user_id: str) -> Player | None:
        """Callback to reload the user object from the user ID stored in the session."""
        app.logger.debug(
            f"Flask-Login: Attempting to load user (Player) with ID: {user_id}"
        )
        # Basic validation of the ID format
        if not user_id or not user_id.isdigit():
            app.logger.warning(
                f"Flask-Login: Invalid user ID format received from session: '{user_id}'"
            )
            return None
        try:
            # Use db.session.get for efficient primary key lookup
            # Must be done within an app context if called outside a request
            # Flask-Login usually handles this automatically within a request context
            user = db.session.get(Player, int(user_id))
            if user:
                app.logger.debug(f"Flask-Login: User {user_id} loaded successfully.")
                return user
            else:
                app.logger.warning(
                    f"Flask-Login: User {user_id} not found in database."
                )
                return None
        except Exception as e:
            app.logger.error(
                f"Flask-Login: Database error while loading user {user_id}: {e}",
                exc_info=True,
            )
            return None  # Safely return None on error

    login_manager.login_view = "auth.login"  # Route name for the login page
    login_manager.login_message = "Effettua il login per accedere a questa pagina." # Messaggio aggiornato
    login_manager.login_message_category = "info"  # Flash message category
    # Optional: Customize session protection level ('basic' or 'strong')
    # login_manager.session_protection = "strong"
    app.logger.info("Flask-Login user_loader, login_view, and messages configured.")

    # --- 7. Register Jinja2 Filters ---
    try:
        register_filters(app)
        app.logger.info("Custom Jinja2 filters registered successfully.")
    except Exception as e:
        app.logger.error(
            f"Warning: Error registering Jinja2 filters: {e}", exc_info=True
        )

    # --- 8. Register Blueprints ---
    try:
        with app.app_context():
            # Register main application blueprints via init_routes
            init_routes(app)
            app.logger.info("Main application blueprints registered (via init_routes).")

            # Explicitly register auth blueprint for clarity, check if already done
            try:
                # NOTA: init_routes probabilmente importa già auth_bp,
                # ma questo è un controllo di sicurezza.
                from app.routes.auth import auth_bp 

                if "auth" not in app.blueprints:
                    app.register_blueprint(auth_bp, url_prefix="/auth")
                    app.logger.info(
                        "Auth blueprint explicitly registered at URL prefix /auth."
                    )
                else:
                    app.logger.debug(
                        "Auth blueprint was already registered (likely via init_routes)."
                    )
            except ImportError:
                app.logger.error(
                    "Auth blueprint (auth_bp) not found. Skipping explicit registration."
                )

            # --- INIZIO MODIFICA: Registrazione API Blueprint ---
            try:
                from app.routes.api.avatar_routes import api_bp
                
                if "api" not in app.blueprints:
                    app.register_blueprint(api_bp, url_prefix="/api/v1")
                    app.logger.info(
                        "API blueprint (api_bp) registered at URL prefix /api/v1."
                    )
                else:
                    app.logger.debug(
                        "API blueprint was already registered."
                    )
            except ImportError:
                app.logger.error(
                    "API blueprint (api_bp) not found in app.routes.api. Skipping registration."
                )
            # --- FINE MODIFICA ---

    except Exception as e:
        app.logger.critical(
            f"FATAL: Error during blueprint registration: {e}", exc_info=True
        )
        raise RuntimeError(f"Failed to register blueprints: {e}")

    # --- 9. Register Error Handlers ---
    try:
        register_error_handlers(app)
        app.logger.info("Custom HTTP error handlers (404, 500, etc.) registered.")
    except Exception as e:
        app.logger.error(
            f"Warning: Error registering custom error handlers: {e}", exc_info=True
        )

    # --- 10. Request Hooks (Optional) ---
    # Example: Log request details
    @app.before_request
    def log_request_info():
        # Avoid logging static file requests if too noisy
        # Now 'request' is imported and available
        if current_app.debug and request.endpoint != "static":
            # Check if request has path attribute, useful for edge cases like websocket setup
            path = getattr(request, "path", "N/A")
            method = getattr(request, "method", "N/A")
            app.logger.debug(f"Handling request: {method} {path}")
            # Log headers or data carefully if needed, avoid sensitive info
            # app.logger.debug(f'Request Headers: {request.headers}')

    # Example: Ensure database session is removed after each request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        # Flask-SQLAlchemy's scoped session usually handles this automatically.
        # Explicit removal can sometimes help prevent stale session issues in complex setups.
        # db.session.remove() # Uncomment if you encounter session problems
        pass

    app.logger.debug("Request hooks (before_request, teardown_appcontext) registered.")

    # --- 11. Final Log Message & Return ---
    app.logger.info(
        f"===> Flask application '{app.name}' created and configured successfully for ENV='{app.config.get('ENV', 'unknown').upper()}' <==="
    )

    # Log registered routes only if in debug mode (can be verbose)
    if app.debug:
        log_url_map(app)

    return app


# Helper function to log URL map (moved outside create_app)
def log_url_map(app: Flask):
    """Logs all registered URL rules for the Flask app in a readable format."""
    # This function is safe to call only after app creation and blueprint registration
    if not app or not hasattr(app, "url_map"):
        app.logger.error("log_url_map called without a valid Flask app instance.")
        return

    try:
        # No need to import flask again, use the app instance
        import urllib.parse

        output = ["--- Registered URL Rules ---"]
        # Sort rules by endpoint name for consistency
        rules = sorted(app.url_map.iter_rules(), key=lambda r: r.endpoint)
        max_len_ep = max(len(r.endpoint) for r in rules) if rules else 0
        # Include HEAD/OPTIONS which are often implicit
        all_methods = set()
        for rule in rules:
            all_methods.update(rule.methods)
        max_len_methods = (
            max(
                len(
                    ",".join(
                        sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
                    )
                )
                for rule in rules
            )
            if rules
            else 0
        )

        for rule in rules:
            # Create placeholder options for url_for
            options = {arg: f"<{arg}>" for arg in rule.arguments}
            # Filter out common implicit methods unless they are the only ones
            methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
            if (
                not methods
            ):  # Handle case like redirects which might only have HEAD/OPTIONS
                methods = sorted(rule.methods)
            methods_str = ",".join(methods)

            try:
                # Generate URL using endpoint name and placeholders within app context
                # Need app context for url_for outside of a request
                with app.app_context():
                    url = urllib.parse.unquote(url_for(rule.endpoint, **options))
            except Exception as url_exc:
                # Fallback if url_for needs specific args not easily mockable
                app.logger.debug(
                    f"Could not generate URL for endpoint '{rule.endpoint}': {url_exc}"
                )
                url = rule.rule  # Show the raw rule string as fallback

            # Format for better alignment
            line = f"{rule.endpoint:<{max_len_ep+2}} {methods_str:<{max_len_methods+2}} {url}"
            output.append(line)

        output.append(f"--- Total Rules: {len(rules)} ---")

        for line in output:
            # Use debug level for potentially verbose output
            app.logger.debug(line)

    except Exception as e:
        app.logger.error(
            f"Could not generate or log URL map: {e}", exc_info=True
        )  # Log traceback on error