import pytest
import os
import importlib
from click.testing import CliRunner
from unittest.mock import MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Imposta la variabile d'ambiente *PRIMA* di importare 'commands'
os.environ["PYTEST_RUNNING"] = "1"

# Importa i modelli e il db di TEST
from app.models import Player, Role
from app import db as test_db

# Importa solo la funzione di registrazione
from commands import register_commands


@pytest.fixture(scope="module")
def cli_app(app):
    """
    Questa fixture registra i comandi CLI dalla logica di 'commands.py'
    direttamente sulla *nostra app di test* (da conftest.py).
    Questo unifica l'app e il database.
    """
    # Assicura che i comandi non siano già registrati
    if not hasattr(app, "_commands_registered"):
        register_commands(app)
        app._commands_registered = True  # Flag per evitare doppie registrazioni
    return app


@pytest.fixture
def runner(cli_app):
    """Fixture per il CLI Runner."""
    return cli_app.test_cli_runner()


@pytest.fixture
def cli_db_session(db_session):
    """Usa la db_session standard di conftest.py."""
    yield db_session


# === Test per 'init-roles' ===


def test_init_roles_success(runner, cli_app, cli_db_session):
    """Testa 'flask init-roles' su un DB pulito."""
    cli_db_session.query(Role).delete()
    cli_db_session.commit()

    # Invoca il comando usando il nome
    result = runner.invoke(cli_app.cli.commands["init-roles"])

    assert result.exit_code == 0
    # CORREZIONE: Output corretto
    assert "Successfully created roles: user, admin" in result.output

    roles = cli_db_session.scalars(test_db.select(Role).order_by(Role.name)).all()
    assert len(roles) == 2
    # CORREZIONE: Controlla l'ordine alfabetico
    assert roles[0].name == "admin"
    assert roles[1].name == "user"


def test_init_roles_already_exist(runner, cli_app, cli_db_session):
    """Testa 'flask init-roles' quando i ruoli esistono già."""
    runner.invoke(cli_app.cli.commands["init-roles"])  # Esegui una prima volta
    result = runner.invoke(cli_app.cli.commands["init-roles"])  # Esegui la seconda

    assert result.exit_code == 0
    assert "Default roles 'admin' and 'user' already exist." in result.output


def test_init_roles_exception(runner, cli_app, cli_db_session, mocker):
    """Testa 'flask init-roles' con un errore DB."""
    # Mocka la funzione create_default_roles
    mocker.patch(
        "commands.create_default_roles", side_effect=SQLAlchemyError("DB Error")
    )

    result = runner.invoke(cli_app.cli.commands["init-roles"])

    assert result.exit_code == 0
    assert "ERROR during role initialization: DB Error" in result.output


# === Test per 'create-admin' e 'create-user' ===


@pytest.fixture
def roles_in_db(runner, cli_app, cli_db_session):
    """Assicura che i ruoli esistano nel DB."""
    cli_db_session.query(Role).delete()
    cli_db_session.commit()
    runner.invoke(cli_app.cli.commands["init-roles"])


class TestCreatePlayerCommands:
    def test_create_admin_success(self, runner, cli_app, roles_in_db, cli_db_session):
        """Testa 'flask create-admin' con successo."""
        args = [
            "--nickname",
            "test_admin",
            "--email",
            "admin@test.com",
            "--password",
            "ValidPassword123",
            "--first-name",
            "Test",
            "--last-name",
            "Admin",
        ]
        result = runner.invoke(cli_app.cli.commands["create-admin"], args)

        assert result.exit_code == 0
        assert "✅ ADMIN player 'test_admin'" in result.output

        player = cli_db_session.scalar(
            test_db.select(Player).filter_by(nickname="test_admin")
        )
        assert player is not None
        assert player.check_password("ValidPassword123") is True
        assert "admin" in [r.name for r in player.roles]

    def test_create_user_success(self, runner, cli_app, roles_in_db, cli_db_session):
        """Testa 'flask create-user' con successo."""
        args = [
            "--nickname",
            "test_user",
            "--email",
            "user@test.com",
            "--password",
            "ValidPassword123",
            "--first-name",
            "Test",
            "--last-name",
            "User",
            "--country",
            "IT",
        ]
        result = runner.invoke(cli_app.cli.commands["create-user"], args)

        assert result.exit_code == 0
        assert "✅ USER player 'test_user'" in result.output

        player = cli_db_session.scalar(
            test_db.select(Player).filter_by(nickname="test_user")
        )
        assert player is not None
        assert player.country == "IT"
        assert "user" in [r.name for r in player.roles]

    @pytest.mark.parametrize(
        "command_name, args, error_msg",
        [
            (
                "create-admin",
                ["--nickname", "t", "--email", "a@b.com", "--password", "12345678"],
                "Error: Nickname is required (min 3 chars).",
            ),
            (
                "create-admin",
                ["--nickname", "test", "--email", "bad", "--password", "12345678"],
                "Error: Valid email is required.",
            ),
            (
                "create-admin",
                ["--nickname", "test", "--email", "a@b.com", "--password", "123"],
                "Error: Password is required (min 8 chars).",
            ),
            (
                "create-admin",
                [
                    "--nickname",
                    "test",
                    "--email",
                    "a@b.com",
                    "--password",
                    "12345678",
                    "--country",
                    "USA",
                ],
                "Error: Country code must be 2 letters.",
            ),
        ],
    )
    def test_create_player_validation_fail(
        self, runner, cli_app, roles_in_db, command_name, args, error_msg
    ):
        """Testa i fallimenti di validazione base (righe 168-181)."""
        result = runner.invoke(cli_app.cli.commands[command_name], args)
        assert result.exit_code == 0  # Il comando gestisce l'errore
        assert error_msg in result.output

    def test_create_admin_no_role_fail(self, runner, cli_app, cli_db_session):
        """Testa 'create-admin' quando il ruolo 'admin' non esiste (righe 185-191)."""
        cli_db_session.query(Role).delete()
        cli_db_session.commit()

        args = [
            "--nickname",
            "test_admin",
            "--email",
            "a@b.com",
            "--password",
            "12345678",
        ]
        result = runner.invoke(cli_app.cli.commands["create-admin"], args)

        assert result.exit_code == 0
        assert (
            "Error: 'admin' role not found. Run 'flask init-roles' first."
            in result.output
        )

    def test_create_user_no_role_fail(self, runner, cli_app, cli_db_session):
        """Testa 'create-user' quando il ruolo 'user' non esiste."""
        cli_db_session.query(Role).delete()
        cli_db_session.commit()

        args = [
            "--nickname",
            "test_user",
            "--email",
            "a@b.com",
            "--password",
            "12345678",
            "--first-name",
            "a",
            "--last-name",
            "b",
        ]
        result = runner.invoke(cli_app.cli.commands["create-user"], args)

        assert result.exit_code == 0
        assert (
            "Error: 'user' role not found. Run 'flask init-roles' first."
            in result.output
        )

    def test_create_player_duplicate_fail(
        self, runner, cli_app, roles_in_db, cli_db_session
    ):
        """Testa 'create-admin' quando l'utente esiste già (righe 193-204)."""
        args = [
            "--nickname",
            "existing",
            "--email",
            "exist@test.com",
            "--password",
            "12345678",
            "--first-name",
            "a",
            "--last-name",
            "b",
        ]
        runner.invoke(cli_app.cli.commands["create-user"], args)

        admin_args = [
            "--nickname",
            "new_admin",
            "--email",
            "exist@test.com",
            "--password",
            "12345678",
        ]
        result = runner.invoke(cli_app.cli.commands["create-admin"], admin_args)

        assert result.exit_code == 0
        assert (
            "Error: Player with nickname 'new_admin' or email 'exist@test.com' already exists."
            in result.output
        )

        player = cli_db_session.scalar(
            test_db.select(Player).filter_by(nickname="existing")
        )
        cli_db_session.delete(player)
        cli_db_session.commit()

    def test_create_player_model_validation_error(
        self, runner, cli_app, roles_in_db, mocker
    ):
        """Testa il blocco 'except ValueError' (riga 228)."""

        # CORREZIONE:
        # 1. Patcha il nome "Player" come usato nel modulo "commands" ("commands.Player").
        # 2. Usa new_callable=mocker.PropertyMock per patchare correttamente
        #    la property .password (il suo setter).
        mocker.patch(
            "commands.Player.password",
            new_callable=mocker.PropertyMock,
            side_effect=ValueError("Model Validation Error"),
        )

        args = [
            "--nickname",
            "test_validation",
            "--email",
            "valid@test.com",
            "--password",
            "ValidPassword123",
            "--first-name",
            "a",
            "--last-name",
            "b",
        ]
        result = runner.invoke(cli_app.cli.commands["create-user"], args)

        assert result.exit_code == 0
        # Ora il test cercherà l'errore corretto
        assert "Validation Error: Model Validation Error" in result.output
        # E verifichiamo che il messaggio di successo NON ci sia
        assert "✅ USER player 'test_validation'" not in result.output

    def test_create_player_integrity_error(self, runner, cli_app, roles_in_db, mocker):
        """Testa il blocco 'except IntegrityError' (riga 235)."""
        mocker.patch.object(
            test_db.session,
            "commit",
            side_effect=IntegrityError("Duplicate", "params", "orig"),
        )

        args = [
            "--nickname",
            "test_integrity",
            "--email",
            "integrity@test.com",
            "--password",
            "ValidPassword123",
            "--first-name",
            "a",
            "--last-name",
            "b",
        ]
        result = runner.invoke(cli_app.cli.commands["create-user"], args)

        assert result.exit_code == 0
        assert (
            "Error: Player with nickname 'test_integrity' or email 'integrity@test.com' likely already exists."
            in result.output
        )

    def test_create_player_generic_exception(
        self, runner, cli_app, roles_in_db, mocker
    ):
        """Testa il blocco 'except Exception' (riga 244)."""
        mocker.patch.object(
            test_db.session, "commit", side_effect=Exception("Generic DB Error")
        )

        args = [
            "--nickname",
            "test_generic",
            "--email",
            "generic@test.com",
            "--password",
            "ValidPassword123",
            "--first-name",
            "a",
            "--last-name",
            "b",
        ]
        result = runner.invoke(cli_app.cli.commands["create-user"], args)

        assert result.exit_code == 0
        assert "ERROR creating player: Generic DB Error" in result.output


# === Test per 'list-users' ===


class TestListUsersCommand:
    def test_list_users_empty(self, runner, cli_app, cli_db_session):
        """Testa 'flask list-users' quando il DB è vuoto (riga 272)."""
        cli_db_session.query(Player).delete()
        cli_db_session.commit()

        result = runner.invoke(cli_app.cli.commands["list-users"])

        assert result.exit_code == 0
        assert "No users found." in result.output

    def test_list_users_with_data(self, runner, cli_app, roles_in_db, cli_db_session):
        """Testa 'flask list-users' con dati (righe 276-291)."""
        cli_db_session.query(Player).delete()
        cli_db_session.commit()

        admin_args = [
            "--nickname",
            "test_admin",
            "--email",
            "admin@test.com",
            "--password",
            "ValidPassword123",
            "--first-name",
            "Test",
            "--last-name",
            "Admin",
        ]
        runner.invoke(cli_app.cli.commands["create-admin"], admin_args)
        user_args = [
            "--nickname",
            "test_user",
            "--email",
            "user@test.com",
            "--password",
            "ValidPassword123",
            "--first-name",
            "Test",
            "--last-name",
            "User",
        ]
        runner.invoke(cli_app.cli.commands["create-user"], user_args)

        result = runner.invoke(cli_app.cli.commands["list-users"])

        assert result.exit_code == 0
        assert "Nick: test_admin" in result.output
        assert "Roles: [admin]" in result.output
        assert "Nick: test_user" in result.output
        assert "Roles: [user]" in result.output
        assert "Total: 2" in result.output
        # CORREZIONE: Rimosso il test per 'is_active' che non c'è più
        assert "Activated: Yes (Password Set)" in result.output

    def test_list_users_filter_role(self, runner, cli_app, roles_in_db, cli_db_session):
        """Testa 'flask list-users --role admin' (riga 267)."""
        cli_db_session.query(Player).delete()
        cli_db_session.commit()

        # CORREZIONE: I nickname 'a' e 'b' erano troppo corti (min 3 chars).
        # Usiamo nickname validi.
        admin_args = [
            "--nickname",
            "admin_user",
            "--email",
            "a@a.com",
            "--password",
            "12345678",
        ]
        user_args = [
            "--nickname",
            "normal_user",
            "--email",
            "b@b.com",
            "--password",
            "12345678",
            "--first-name",
            "f",
            "--last-name",
            "l",
        ]

        runner.invoke(cli_app.cli.commands["create-admin"], admin_args)
        runner.invoke(cli_app.cli.commands["create-user"], user_args)

        result = runner.invoke(cli_app.cli.commands["list-users"], ["--role", "admin"])

        assert result.exit_code == 0
        assert "Nick: admin_user" in result.output  # <-- Controlla il nickname corretto
        assert "Nick: normal_user" not in result.output
        assert "Total: 1" in result.output

    def test_list_users_filter_no_match(
        self, runner, cli_app, roles_in_db, cli_db_session
    ):
        """Testa 'flask list-users --role <nonesiste>'."""
        cli_db_session.query(Player).delete()
        cli_db_session.commit()

        # CORREZIONE: Anche qui il nickname 'b' non era valido (min 3 chars).
        user_args = [
            "--nickname",
            "some_user",
            "--email",
            "b@b.com",
            "--password",
            "12345678",
            "--first-name",
            "f",
            "--last-name",
            "l",
        ]
        runner.invoke(cli_app.cli.commands["create-user"], user_args)

        result = runner.invoke(
            cli_app.cli.commands["list-users"], ["--role", "nonexistent"]
        )
        assert result.exit_code == 0
        assert "No users found with role nonexistent" in result.output

    def test_list_users_exception(self, runner, cli_app, cli_db_session, mocker):
        """Testa 'flask list-users' con un errore DB (riga 293)."""
        mocker.patch.object(
            test_db.session, "scalars", side_effect=SQLAlchemyError("DB Error")
        )

        result = runner.invoke(cli_app.cli.commands["list-users"])
        assert result.exit_code == 0
        assert "ERROR listing users: DB Error" in result.output
