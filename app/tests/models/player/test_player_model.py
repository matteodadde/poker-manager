import pytest
from app.models import Player
from app.models.roles import Role
import uuid
import sqlalchemy.exc
import datetime


@pytest.fixture
def base_player_data():
    """
    Fixture per i dati di base di un giocatore.
    Genera email e nickname UNICI per ogni test.
    Rappresenta un utente con 'password_hash' nullo (pending).
    """
    unique_id = uuid.uuid4().hex[:8]
    return {
        "first_name": "Mario",
        "last_name": "Rossi",
        "nickname": f"mario_rossi_{unique_id}",
        "email": f"mario.rossi.{unique_id}@test.com",
        "country": "IT",
    }


@pytest.fixture
def sample_roles(db_session):
    """Fixture per creare ruoli 'admin' e 'user'."""
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin")

    user_role = Role.query.filter_by(name="user").first()
    if not user_role:
        user_role = Role(name="user")

    db_session.add_all([admin_role, user_role])
    db_session.commit()
    return {"admin": admin_role, "user": user_role}


def test_create_player(db_session, base_player_data):
    """Verifica la creazione di un giocatore base (senza password)."""
    player = Player(**base_player_data)
    db_session.add(player)
    db_session.commit()

    assert player.id is not None
    assert player.first_name == "Mario"
    assert player.password_hash is None
    assert player.nickname == base_player_data["nickname"]


def test_repr_pending_activation(db_session, base_player_data):
    """
    Verifica il __repr__ di un giocatore in attesa di "attivazione"
    (cioè senza password_hash).
    """
    player = Player(**base_player_data)
    db_session.add(player)
    db_session.commit()

    expected = (
        f"<Player id={player.id} nickname={repr(player.nickname)} "
        f"email={repr(player.email)} roles=[None] status=Active "
        f"activated=No (Pending Activation)>"
    )

    assert repr(player) == expected


@pytest.mark.parametrize(
    "field,value,error_msg",
    [
        # --- Test Nomi ---
        ("first_name", "", "Il First Name non può essere vuoto"),
        ("first_name", "          ", "Il First Name non può essere vuoto"),
        ("first_name", "a" * 51, "Il First Name non può superare i 50 caratteri"),
        ("first_name", "matteo1", "Il First Name non può contenere numeri"),
        ("last_name", "", "Il Last Name non può essere vuoto"),
        ("last_name", "      ", "Il Last Name non può essere vuoto"),
        ("last_name", "b" * 51, "Il Last Name non può superare i 50 caratteri"),
        ("last_name", "rossi1", "Il Last Name non può contenere numeri"),
        # --- Test Nickname ---
        ("nickname", "", "Il nickname non può essere vuoto"),
        ("nickname", "ab", "Il nickname deve essere tra 3 e 50 caratteri"),
        ("nickname", "a" * 51, "Il nickname deve essere tra 3 e 50 caratteri"),
        (
            "nickname",
            "inv@lid",
            "Il nickname può contenere solo lettere, numeri, '.', '_' o '-'",
        ),
        # --- Test Country ---
        (
            "country",
            "XYZ",
            "Il codice paese deve essere un codice ISO a 2 lettere (es. IT)",
        ),
        # --- Test Email (Corretti) ---
        ("email", "", "L'email non può essere vuota"),
        ("email", "     ", "L'email non può essere vuota"),
        ("email", "not-an-email", "Formato email non valido"),
        ("email", "invalid@domain", "Formato email non valido"),
        # --- MODIFICA ---
        # 112 + 9 = 121 caratteri. Questo ora fallirà correttamente.
        ("email", f"{'a'*112}@test.com", "L'email non può superare i 120 caratteri"),
    ],
)
def test_field_validations(base_player_data, field, value, error_msg):
    """Testa le validazioni dei campi."""
    data = base_player_data.copy()
    data[field] = value

    if field != "nickname":
        data["nickname"] = f"unique_nick_for_{field}"
    if field != "email":
        data["email"] = f"unique_email_for_{field}@test.com"

    with pytest.raises(ValueError) as excinfo:
        Player(**data)

    assert error_msg in str(excinfo.value)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("it", "IT"),
        ("IT", "IT"),
        (None, None),
        ("", None),
        ("  ", None),
    ],
)
def test_country_case_insensitive(db_session, base_player_data, value, expected):
    """Verifica la normalizzazione del campo 'country'."""
    data = base_player_data.copy()
    data["country"] = value

    player = Player(**data)
    db_session.add(player)
    db_session.commit()

    assert player.country == expected


def test_unique_nickname(db_session, base_player_data):
    """Verifica il vincolo di unicità del nickname."""
    data_player1 = base_player_data
    player1 = Player(**data_player1)
    db_session.add(player1)
    db_session.commit()

    data2 = {
        "first_name": "Luigi",
        "last_name": "Bianchi",
        "nickname": data_player1["nickname"],
        "email": f"luigi.bianchi.{uuid.uuid4().hex[:8]}@test.com",
        "country": "IT",
    }

    player2 = Player(**data2)
    db_session.add(player2)

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_password_methods(db_session, base_player_data):
    """Testa il setter della password, il check e l'errore di lettura."""
    player = Player(**base_player_data)
    db_session.add(player)
    db_session.commit()

    assert player.password_hash is None
    assert player.check_password("strongP@ss1") is False

    player.password = "strongP@ss1"
    db_session.commit()

    assert player.password_hash is not None
    assert player.check_password("strongP@ss1") is True
    assert player.check_password("wrongpass") is False

    with pytest.raises(AttributeError, match="Password is not a readable attribute"):
        _ = player.password


@pytest.mark.parametrize(
    "password, error_msg",
    [
        ("weak", "La password deve essere di almeno 8 caratteri"),
        ("", "La password non può essere vuota"),
        (None, "La password non può essere vuota"),
    ],
)
def test_password_strength_validation(base_player_data, password, error_msg):
    """Testa i validatori della password per 'empty' e 'length'."""
    player = Player(**base_player_data)

    with pytest.raises(ValueError, match=error_msg):
        player.password = password


def test_role_methods(db_session, base_player_data, sample_roles):
    """Testa i metodi helper 'has_role' e 'is_admin'."""
    player_admin = Player(**base_player_data)
    player_admin.roles.append(sample_roles["admin"])
    player_admin.roles.append(sample_roles["user"])

    data2 = base_player_data.copy()
    uid = uuid.uuid4().hex[:8]
    data2["nickname"] = f"test_user_{uid}"
    data2["email"] = f"test_user_{uid}@test.com"
    player_user = Player(**data2)
    player_user.roles.append(sample_roles["user"])

    db_session.add_all([player_admin, player_user])
    db_session.commit()

    assert player_admin.has_role("admin") is True
    assert player_admin.has_role("user") is True
    assert player_admin.has_role("ADMIN") is True
    assert player_admin.has_role("guest") is False
    assert player_admin.is_admin is True

    assert player_user.has_role("admin") is False
    assert player_user.has_role("user") is True
    assert player_user.is_admin is False


def test_repr_activated_and_roles(db_session, base_player_data, sample_roles):
    """Verifica il __repr__ di un giocatore ATTIVATO e con ruoli."""
    player = Player(**base_player_data)
    player.password = "MyP@ss123"
    player.roles.append(sample_roles["admin"])
    player.roles.append(sample_roles["user"])

    db_session.add(player)
    db_session.commit()

    repr_str = repr(player)

    assert f"id={player.id}" in repr_str
    assert f"nickname={repr(player.nickname)}" in repr_str
    assert "status=Active" in repr_str
    assert "activated=Yes" in repr_str
    assert "admin" in repr_str
    assert "user" in repr_str
    assert "roles=[" in repr_str
