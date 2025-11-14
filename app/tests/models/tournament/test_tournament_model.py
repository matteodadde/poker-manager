import pytest
from datetime import date, datetime
from decimal import Decimal
import sqlalchemy.exc
from app.models import Tournament, Player, TournamentPlayer
from app import db


def test_create_tournament_and_repr(db_session, sample_player):
    """
    Testa la creazione di un torneo valido (con admin_id)
    e la sua rappresentazione __repr__.
    """
    admin = sample_player["player"]

    tournament = Tournament(
        name="Torneo Principale",
        tournament_date=date(2025, 10, 20),
        buy_in=Decimal("100.00"),
        location="Casino Centrale",
        prize_pool=None,
        admin_id=admin.id,
    )
    db_session.add(tournament)
    db_session.commit()

    assert tournament.id is not None
    assert tournament.name == "Torneo Principale"
    assert tournament.admin_id == admin.id
    assert tournament.prize_pool is None

    expected_repr = f"<Tournament(id={tournament.id}, name='Torneo Principale', date={date(2025, 10, 20)})>"
    assert repr(tournament) == expected_repr


@pytest.mark.parametrize(
    "field, value, error_msg",
    [
        ("name", None, "Il nome del torneo non può essere vuoto."),
        ("name", "", "Il nome del torneo non può essere vuoto."),
        ("name", "   ", "Il nome del torneo non può essere vuoto."),
        ("name", "a" * 101, "Il nome del torneo non può superare i 100 caratteri."),
        ("buy_in", 0, "Il buy-in deve essere maggiore di zero."),
        ("buy_in", -10, "Il buy-in deve essere maggiore di zero."),
        ("buy_in", "invalid", "Il buy-in deve essere un numero decimale valido."),
        ("prize_pool", -100, "Il prize_pool non può essere negativo."),
        (
            "prize_pool",
            "invalid",
            "Il prize_pool deve essere un numero decimale valido.",
        ),
        ("location", "a" * 151, "La location non può superare i 150 caratteri."),
        ("tournament_date", "01-01-2025", "o una stringa in formato ISO"),
        ("tournament_date", 12345, "o una stringa in formato ISO"),
    ],
)
def test_tournament_field_validations(
    db_session, sample_player, field, value, error_msg
):
    """Testa tutti i validatori (ValueError) del modello Tournament."""
    admin_id = sample_player["player"].id

    data = {
        "name": "Torneo Valido",
        "tournament_date": date(2025, 1, 1),
        "buy_in": Decimal("50.00"),
        "admin_id": admin_id,
    }

    data[field] = value

    with pytest.raises(ValueError, match=error_msg):
        Tournament(**data)


def test_valid_none_or_empty_fields(db_session, sample_player):
    """Testa che i campi opzionali (location, prize_pool) accettino None/stringhe vuote."""
    admin_id = sample_player["player"].id

    t1 = Tournament(
        name="Test 1",
        tournament_date=date(2025, 1, 1),
        buy_in=100,
        admin_id=admin_id,
        prize_pool=None,
    )
    assert t1.prize_pool is None

    t2 = Tournament(
        name="Test 2",
        tournament_date=date(2025, 1, 1),
        buy_in=100,
        admin_id=admin_id,
        location=None,
    )
    assert t2.location is None

    t3 = Tournament(
        name="Test 3",
        tournament_date=date(2025, 1, 1),
        buy_in=100,
        admin_id=admin_id,
        location="   ",
    )
    assert t3.location is None


def test_tournament_date_converts_datetime(sample_player):
    """Testa che un datetime venga convertito in date."""
    admin_id = sample_player["player"].id
    dt = datetime(2025, 10, 5, 18, 30, 0)

    t = Tournament(
        name="Test Datetime", tournament_date=dt, buy_in=100, admin_id=admin_id
    )
    assert t.tournament_date == date(2025, 10, 5)


def test_tournament_db_constraints(db_session, sample_player):
    """
    Testa i vincoli NOT NULL del database (IntegrityError).
    """
    admin_id = sample_player["player"].id

    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match="NOT NULL constraint failed: tournament.admin_id",
    ):
        t1 = Tournament(name="Test", tournament_date=date(2025, 1, 1), buy_in=100)
        db_session.add(t1)
        db_session.commit()
    db_session.rollback()


def test_admin_relationship(db_session, sample_player):
    """Testa la relazione tournament.admin (lazy='joined')."""
    admin = sample_player["player"]

    tournament = Tournament(
        name="Torneo di Admin",
        tournament_date=date(2025, 1, 1),
        buy_in=100,
        admin_id=admin.id,
    )
    db_session.add(tournament)
    db_session.commit()

    t_from_db = db_session.get(Tournament, tournament.id)

    assert t_from_db.admin is not None
    assert t_from_db.admin.id == admin.id
    assert t_from_db.admin.nickname == admin.nickname


def test_num_players_property(
    db_session, multiple_players, create_tournament, add_participation
):
    """
    Testa la property @cached_property 'num_players'.
    """
    tournament = create_tournament()

    # 2. Testa con 0 giocatori
    db_session.refresh(tournament)
    assert tournament.num_players == 0  # La cache viene impostata a 0

    # 3. Aggiungi 3 giocatori
    players = multiple_players(3)
    for player in players:
        add_participation(player, tournament)

    # 4. Ricarica e testa

    # --- MODIFICA DEFINITIVA ---
    # Invalida manualmente la cache.
    try:
        del tournament.num_players
    except AttributeError:
        pass  # OK se non era ancora in cache
    # --- FINE MODIFICA ---

    # Ora la property DEVE ricalcolarsi dal DB
    assert tournament.num_players == 3
    assert len(tournament.tournament_players) == 3
