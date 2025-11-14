import pytest
import sqlalchemy.exc
from sqlalchemy import func
from app import db  # Importa 'db'
from app.models import Player, Role
from app.models.roles import roles_players, create_default_roles


@pytest.fixture(autouse=True)
def clean_roles(db_session):
    """
    Pulisce i ruoli e la tabella associativa DOPO ogni test.
    Questo è necessario perché create_default_roles() esegue un commit,
    bypassando il rollback della fixture db_session.
    """
    yield
    # Pulisce la tabella Role e la tabella associativa dopo il test
    # Esegui in ordine inverso per rispettare i foreign key
    db_session.query(roles_players).delete()
    db_session.query(Role).delete()
    db_session.commit()


def test_create_role(db_session):
    """Testa la creazione di un ruolo e il suo __repr__."""
    role = Role(name="test_admin", description="Administrator")
    db_session.add(role)
    db_session.commit()

    assert role.id is not None
    assert role.name == "test_admin"
    assert role.description == "Administrator"

    expected_repr = f"<Role id={role.id} name='test_admin'>"
    assert repr(role) == expected_repr


def test_role_name_unique_constraint(db_session):
    """Testa che il nome del ruolo sia unico."""
    role1 = Role(name="test_user")
    db_session.add(role1)
    db_session.commit()

    role2 = Role(name="test_user")
    db_session.add(role2)

    with pytest.raises(
        sqlalchemy.exc.IntegrityError, match="UNIQUE constraint failed: role.name"
    ):
        db_session.commit()

    db_session.rollback()


def test_role_name_not_nullable_constraint(db_session):
    """Testa che il nome del ruolo non possa essere nullo."""
    role = Role(name=None, description="Ruolo nullo")
    db_session.add(role)

    with pytest.raises(
        sqlalchemy.exc.IntegrityError, match="NOT NULL constraint failed: role.name"
    ):
        db_session.commit()

    db_session.rollback()


def test_role_player_relationship(db_session, sample_player):
    """Testa la relazione many-to-many tra Role e Player."""
    player = sample_player["player"]
    admin_role = Role(name="test_admin_rel")
    user_role = Role(name="test_user_rel")

    player.roles.append(admin_role)
    player.roles.append(user_role)

    db_session.add(player)
    db_session.commit()

    db_session.refresh(player)
    db_session.refresh(admin_role)

    assert len(player.roles) == 2
    assert admin_role in player.roles
    assert user_role in player.roles

    assert len(admin_role.players) == 1
    assert player in admin_role.players


def test_create_default_roles_empty_db(db_session, app):
    """Testa la funzione create_default_roles() su un database vuoto."""
    count_before = db_session.scalar(db.select(func.count(Role.id)))
    assert count_before == 0

    with app.app_context():
        create_default_roles()

    count_after = db_session.scalar(db.select(func.count(Role.id)))
    assert count_after == 2

    admin = db_session.scalar(db.select(Role).filter_by(name="admin"))

    # --- CORREZIONE DEL REBUSO ---
    user = db_session.scalar(db.select(Role).filter_by(name="user"))

    assert admin is not None
    assert user is not None
    assert admin.description is not None


def test_create_default_roles_partial_db(db_session, app):
    """Testa che la funzione non crei duplicati se un ruolo esiste già."""
    user_role = Role(name="user", description="Descrizione custom")
    db_session.add(user_role)
    db_session.commit()

    count_before = db_session.scalar(db.select(func.count(Role.id)))
    assert count_before == 1

    with app.app_context():
        create_default_roles()

    count_after = db_session.scalar(db.select(func.count(Role.id)))
    assert count_after == 2

    user = db_session.scalar(db.select(Role).filter_by(name="user"))

    # --- CORREZIONE DEL REBUSO ---
    admin = db_session.scalar(db.select(Role).filter_by(name="admin"))

    assert admin is not None
    assert user.description == "Descrizione custom"


def test_create_default_roles_all_exist_db(db_session, app):
    """Testa che la funzione non faccia nulla se entrambi i ruoli esistono già."""
    db_session.add_all(
        [Role(name="user", description="User"), Role(name="admin", description="Admin")]
    )
    db_session.commit()

    count_before = db_session.scalar(db.select(func.count(Role.id)))
    assert count_before == 2

    with app.app_context():
        create_default_roles()

    count_after = db_session.scalar(db.select(func.count(Role.id)))
    assert count_after == 2


# --- NUOVO TEST PER COPRIRE IL BLOCCO EXCEPT ---


def test_create_default_roles_commit_error(db_session, app, mocker):
    """
    Testa il blocco except (righe 98-100)
    simulando un errore durante il commit.
    """
    # Verifica che il DB sia vuoto
    count_before = db_session.scalar(db.select(func.count(Role.id)))
    assert count_before == 0

    # Mock di session.commit per sollevare un'eccezione
    # Dobbiamo mockare 'app.db.session.commit' perché è quello
    # che viene chiamato da 'roles.py'
    mocker.patch("app.db.session.commit", side_effect=Exception("Test Commit Error"))

    # Mock di session.rollback per verificare che venga chiamato
    mock_rollback = mocker.patch("app.db.session.rollback")

    with app.app_context():
        create_default_roles()  # Questa chiamata ora fallirà internamente

    # Verifica che il commit sia stato tentato e il rollback sia stato chiamato
    assert db.session.commit.called
    assert mock_rollback.called

    # Verifica che nessun ruolo sia stato aggiunto (il rollback ha funzionato)
    # Nota: la fixture db_session farebbe comunque un rollback,
    # ma questo test verifica che la *funzione* chiami il rollback.
    count_after = db_session.scalar(db.select(func.count(Role.id)))
    assert count_after == 0
