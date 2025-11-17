# app/routes/players/forms.py
"""
Form WTForms per la modifica dei dati anagrafici dei giocatori (Player).
La gestione dell'avatar è demandata a un endpoint API separato.
"""
from flask_wtf import FlaskForm
# --- MODIFICA: Rimossi FileField e FileAllowed ---
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import (
    DataRequired,
    Length,
    Email,
    EqualTo,
    ValidationError,
    Optional,
    Regexp,
)

from app.models import Player
from app import db

# Lista Paesi (potrebbe stare in config o utils)
LISTA_PAESI = [
    ("", "Seleziona Paese (Opzionale)"),
    ("IT", "Italia"),
    ("US", "Stati Uniti"),
    ("GB", "Regno Unito"),
    ("FR", "Francia"),
    ("DE", "Germania"),
    ("ES", "Spagna"),
]


class PlayerForm(FlaskForm):
    """Form per modificare i dati anagrafici di un giocatore."""

    first_name = StringField(
        "Nome",
        validators=[
            Optional(),
            Length(max=50, message="Massimo 50 caratteri."),
        ],
    )
    last_name = StringField(
        "Cognome",
        validators=[
            Optional(),
            Length(max=50, message="Massimo 50 caratteri."),
        ],
    )
    nickname = StringField(
        "Nickname",
        validators=[
            DataRequired("Il nickname è obbligatorio."),
            Length(min=3, max=50, message="Nickname tra 3 e 50 caratteri."),
            Regexp(
                r"^[\w.-]+$",
                message="Nickname può contenere solo lettere, numeri, '.', '-', '_'",
            ),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired("L'email è obbligatoria."),
            Email("Formato email non valido."),
            Length(max=120, message="Massimo 120 caratteri."),
        ],
    )

    # --- Sezione Password Modificata ---
    old_password = PasswordField(
        "Password Attuale",
        validators=[Optional()],
    )
    password = PasswordField(
        "Nuova Password",
        validators=[
            Optional(),
            Length(
                min=8, message="La nuova password deve essere di almeno 8 caratteri."
            ),
        ],
    )
    confirm_password = PasswordField(
        "Conferma Nuova Password",
        validators=[
            Optional(),
            EqualTo("password", message="Le nuove password devono corrispondere."),
        ],
    )
    
    # --- MODIFICA: Campi avatar rimossi ---
    # avatar = FileField(...)
    # delete_avatar = BooleanField(...)
    # --- FINE MODIFICA ---

    country = SelectField(
        "Paese",
        choices=LISTA_PAESI,
        validators=[Optional()],
    )
    submit = SubmitField("Salva Giocatore")

    # Tiene traccia dei valori originali E dell'oggetto player
    def __init__(
        self,
        original_nickname=None,
        original_email=None,
        player_obj=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.original_nickname = original_nickname
        self.original_email = original_email
        self.player = player_obj

    # Validazione Unicità Nickname (solo se cambiato)
    def validate_nickname(self, field):
        nickname_lower = field.data.strip().lower()
        original_lower = (self.original_nickname or "").lower()
        if nickname_lower != original_lower:
            stmt = db.select(Player).filter(Player.nickname.ilike(nickname_lower))
            if db.session.scalar(stmt):
                raise ValidationError("Nickname già registrato.")

    # Validazione Unicità Email (solo se cambiata)
    def validate_email(self, field):
        email_lower = field.data.strip().lower()
        original_lower = (self.original_email or "").lower()
        if email_lower != original_lower:
            stmt = db.select(Player).filter(Player.email.ilike(email_lower))
            if db.session.scalar(stmt):
                raise ValidationError("Email già registrata.")

    # Validazione customizzata per la logica complessa della password
    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        is_edit_mode = self.player is not None

        old_pwd = self.old_password.data
        new_pwd = self.password.data
        confirm_pwd = self.confirm_password.data

        # 1. MODALITÀ CREAZIONE
        if not is_edit_mode:
            if not new_pwd:
                self.password.errors.append(
                    "La password è obbligatoria per i nuovi giocatori."
                )
                return False
            if not confirm_pwd:
                if new_pwd:
                    self.confirm_password.errors.append("Devi confermare la password.")
                    return False

        # 2. MODALITÀ MODIFICA
        if is_edit_mode:
            if old_pwd or new_pwd or confirm_pwd:
                if not old_pwd:
                    self.old_password.errors.append(
                        "Devi inserire la password attuale per poterla modificare."
                    )
                    return False

                if not self.player.check_password(old_pwd):
                    self.old_password.errors.append("Password attuale non corretta.")
                    return False

                if not new_pwd:
                    self.password.errors.append("Devi inserire la nuova password.")
                    return False

        return True


# Form vuoto per CSRF protection sulla cancellazione.
class DeletePlayerForm(FlaskForm):
    """Form vuoto usato solo per la protezione CSRF nel modal di eliminazione."""

    submit = SubmitField("Elimina Giocatore")