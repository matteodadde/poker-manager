# app/routes/auth/forms.py
"""
WTForms for authentication: Login only.
Account creation/activation is handled via CLI commands.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email

# Rimosse importazioni non più necessarie:
# - Length, EqualTo, ValidationError, Regexp (non usate in LoginForm)
# - Player, db, func (non usate in LoginForm)


class LoginForm(FlaskForm):
    """Form for user login."""

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="L'email è obbligatoria."),
            Email(message="Inserisci un indirizzo email valido."),
        ],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(message="La password è obbligatoria.")]
    )
    remember = BooleanField("Ricordami")
    submit = SubmitField("Accedi")
