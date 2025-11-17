import pytest
from unittest.mock import MagicMock
from app.routes.players.forms import PlayerForm


# Usiamo una fixture per creare un finto Player
# che ci serve per il test della modalità MODIFICA
@pytest.fixture
def mock_player():
    """Crea un mock di un Player con un metodo check_password funzionante."""
    player = MagicMock()

    # Diciamo al mock di restituire True solo se la password è "correct_password"
    player.check_password.side_effect = lambda pwd: pwd == "correct_password"
    return player


# --- Test per la MODALITÀ CREAZIONE (is_edit_mode=False) ---


def test_create_player_form_password_required(app, mocker):  # <-- Aggiunto mocker
    """
    Testa (linee 159-161): In modalità CREAZIONE, se la password è vuota,
    il form deve fallire con l'errore corretto.
    """

    # --- CHIAVE: ---
    # Patchiamo la chiamata 'db.session.scalar' che viene usata
    # DENTRO 'app/routes/players/forms.py' dai validatori.
    # Le facciamo restituire None (come se l'utente non esistesse).
    mocker.patch("app.routes.players.forms.db.session.scalar", return_value=None)

    # WTForms richiede un contesto di richiesta per funzionare
    with app.test_request_context():
        form_data = {
            "nickname": "newuser",
            "email": "new@user.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "",  # <-- Password MANCANTE
            "confirm_password": "",
        }

        form = PlayerForm(
            player_obj=None,  # Modalità CREAZIONE
            original_nickname=None,
            original_email=None,
            data=form_data,
        )

        # Ora la validazione (validate_nickname/email) userà il mock
        # e la validazione iniziale passerà, permettendoci di
        # testare la nostra logica custom.
        assert form.validate() is False

        assert (
            "La password è obbligatoria per i nuovi giocatori." in form.password.errors
        )


# --- Test per la MODALITÀ MODIFICA (is_edit_mode=True) ---
# Questi test sono corretti perché evitano la query al DB
# facendo corrispondere 'original_nickname' e 'data[nickname]'.


def test_edit_player_form_change_password_requires_old_password(app, mock_player):
    """
    Testa (linee 177-179): In MODIFICA, se si inserisce una nuova password
    ma non quella vecchia, il form fallisce.
    """
    with app.test_request_context():
        form_data = {
            "nickname": "testuser",
            "email": "test@user.com",
            "first_name": "Test",
            "last_name": "User",
            "old_password": "",  # <-- Vecchia password MANCANTE
            "password": "new_password_123",
            "confirm_password": "new_password_123",
        }

        form = PlayerForm(
            player_obj=mock_player,  # Modalità MODIFICA
            # Facciamo corrispondere original_ e data per SALTARE la query al DB
            original_nickname="testuser",
            original_email="test@user.com",
            data=form_data,
        )

        assert form.validate() is False
        assert (
            "Devi inserire la password attuale per poterla modificare."
            in form.old_password.errors
        )


def test_edit_player_form_change_password_wrong_old_password(app, mock_player):
    """
    Testa (linee 181-183): In MODIFICA, se la vecchia password inserita
    non è corretta (il mock restituisce False), il form fallisce.
    """
    with app.test_request_context():
        form_data = {
            "nickname": "testuser",
            "email": "test@user.com",
            "first_name": "Test",
            "last_name": "User",
            "old_password": "wrong_password",  # <-- SBAGLIATA
            "password": "new_password_123",
            "confirm_password": "new_password_123",
        }

        form = PlayerForm(
            player_obj=mock_player,  # Modalità MODIFICA
            original_nickname="testuser",
            original_email="test@user.com",
            data=form_data,
        )

        # Il mock_player.check_password("wrong_password") restituirà False
        assert form.validate() is False
        assert "Password attuale non corretta." in form.old_password.errors


def test_edit_player_form_change_password_requires_new_password(app, mock_player):
    """
    Testa (linee 186-188): In MODIFICA, se la vecchia password è corretta
    ma quella nuova è vuota, il form fallisce.
    """
    with app.test_request_context():
        form_data = {
            "nickname": "testuser",
            "email": "test@user.com",
            "first_name": "Test",
            "last_name": "User",
            "old_password": "correct_password",  # <-- CORRETTA
            "password": "",  # <-- Nuova password MANCANTE
            "confirm_password": "",
        }

        form = PlayerForm(
            player_obj=mock_player,  # Modalità MODIFICA
            original_nickname="testuser",
            original_email="test@user.com",
            data=form_data,
        )

        # Il mock_player.check_password("correct_password") restituirà True
        assert form.validate() is False
        assert "Devi inserire la nuova password." in form.password.errors
