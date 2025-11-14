# app/routes/tournaments/forms.py
"""
WTForms for creating and editing Tournaments and their Participants.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DateField,
    DecimalField,
    SubmitField,
    HiddenField,
    SelectField,
    IntegerField,
    FieldList,
    FormField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    Optional,
    ValidationError,
    NumberRange,
)
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

# --- FINE MODIFICA ---


# === Sub-Form for a single participant entry ===
class TournamentPlayerEntryForm(FlaskForm):
    """Sub-form representing a single participant entry."""

    tp_id = HiddenField("Participant ID", validators=[Optional()])
    player_id = SelectField(
        "Player", coerce=int, validators=[DataRequired("Please select a player.")]
    )
    position = IntegerField(
        "Position",
        validators=[
            Optional(),
            NumberRange(min=1, message="Position must be 1 or greater."),
        ],
    )
    rebuy = IntegerField(
        "Rebuys",
        validators=[
            Optional(),
            NumberRange(min=0, message="Rebuys cannot be negative."),
        ],
        default=0,
    )
    rebuy_total_spent = DecimalField(
        "Rebuy Spent (€)",
        validators=[
            Optional(),
            NumberRange(min=0, message="Rebuy total spent cannot be negative."),
        ],
        places=2,
        rounding=ROUND_HALF_UP,
        default=Decimal("0.00"),
    )
    prize = DecimalField(
        "Prize (€)",
        validators=[
            Optional(),
            NumberRange(min=0, message="Prize cannot be negative."),
        ],
        places=2,
        rounding=ROUND_HALF_UP,
        default=Decimal("0.00"),
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("meta", {})
        kwargs["meta"].setdefault(
            "csrf", False
        )  # Corretto: disabilita CSRF per subform
        super().__init__(*args, **kwargs)


class TournamentForm(FlaskForm):
    """Form to create or edit a Tournament and manage its participants."""

    name = StringField(
        "Tournament Name",
        validators=[
            DataRequired("Tournament name is required."),
            Length(
                min=3, max=100, message="Name must be between 3 and 100 characters."
            ),
        ],
    )
    tournament_date = DateField(
        "Date",
        validators=[DataRequired("Date is required.")],
        format="%Y-%m-%d",
        default=date.today,
    )
    buy_in = DecimalField(
        "Buy-in (€)",
        validators=[
            DataRequired("Buy-in is required."),
            NumberRange(min=0, message="Buy-in must be 0 or greater."),
        ],
        places=2,
        rounding=ROUND_HALF_UP,
        default=Decimal("10.00"),
    )
    prize_pool = DecimalField(
        "Fixed Prize Pool (€) (Optional)",
        validators=[
            Optional(),
            NumberRange(min=0, message="Prize pool cannot be negative."),
        ],
        places=2,
        rounding=ROUND_HALF_UP,
    )
    location = StringField(
        "Location (Optional)",
        validators=[Optional(), Length(max=150, message="Max 150 characters.")],
    )
    participants = FieldList(
        FormField(TournamentPlayerEntryForm), min_entries=0, label="Participants"
    )
    submit = SubmitField("Save Tournament")

    def validate_participants(self, field):
        """Checks for duplicate player selections in the participants list."""
        # Ottimo validatore! Questo è il posto giusto per questo controllo.
        player_ids = [entry.player_id.data for entry in field if entry.player_id.data]
        if len(player_ids) != len(set(player_ids)):
            seen = set()
            duplicates = set()
            # Cerca il dizionario delle scelte per ottenere i nomi
            choices_dict = dict(
                self.participants.entries[0].player_id.choices
                if self.participants.entries
                else []
            )
            for pid in player_ids:
                if pid in seen:
                    duplicates.add(choices_dict.get(pid, f"ID {pid}"))
                seen.add(pid)
            raise ValidationError(
                f"Duplicate player(s) selected: {', '.join(duplicates)}. Each player can only be added once."
            )


# Form vuoto per CSRF sulla delete
class DeleteTournamentForm(FlaskForm):
    """CSRF protection form for tournament deletion."""

    submit = SubmitField("Delete Tournament")
