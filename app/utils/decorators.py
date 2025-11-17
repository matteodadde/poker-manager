# app/utils/decorators.py
"""
Decoratori personalizzati per l'applicazione.
"""
from functools import wraps
from flask import abort, current_app
from flask_login import current_user


def admin_required(f):
    """
    Decoratore per restringere l'accesso a una route solo agli amministratori.

    Verifica che l'utente sia loggato e abbia il ruolo 'admin'.
    Se non lo è, interrompe la richiesta con un errore 403 (Forbidden).
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Controlla se l'utente è loggato
        if not current_user.is_authenticated:
            # Flask-Login dovrebbe già gestire questo con @login_required,
            # ma è una doppia sicurezza. Potrebbe reindirizzare al login.
            current_app.logger.warning(
                f"Accesso negato (non autenticato) a {f.__name__}"
            )
            abort(401)  # Unauthorized - Reindirizzerà al login

        # 2. Controlla se l'utente ha il ruolo 'admin'
        # Usiamo la property 'is_admin' che abbiamo aggiunto al modello Player
        if not current_user.is_admin:
            current_app.logger.warning(
                f"Accesso negato (non admin) a {f.__name__} da utente: {current_user.email}"
            )
            abort(403)  # Forbidden - Mostra pagina di errore 403

        # Se entrambi i controlli passano, esegui la funzione originale
        return f(*args, **kwargs)

    return decorated_function
