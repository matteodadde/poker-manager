import pytest
from flask.testing import FlaskClient
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from unittest.mock import MagicMock, patch

# Importa i modelli e il db necessari
from app.models import Player, Role, TournamentPlayer
from app import db, bcrypt  # Importa bcrypt per il test della password


# === Fixture Locale per Admin ===
@pytest.fixture
def admin_client(authenticated_client, db_session, sample_player):
    """
    Restituisce un client autenticato (da authenticated_client)
    a cui è stato appena CONCESSO il ruolo di 'admin'.
    """

    # 1. Assicurati che il ruolo 'admin' esista
    admin_role = db_session.query(Role).filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin")
        db_session.add(admin_role)

    # 2. Assicurati che il ruolo 'user' esista (necessario per il test 'add_player')
    user_role = db_session.query(Role).filter_by(name="user").first()
    if not user_role:
        user_role = Role(name="user")
        db_session.add(user_role)

    db_session.commit()

    # 3. Assegna il ruolo admin al sample_player
    player = sample_player["player"]
    # Pulisci ruoli esistenti se necessario (per idempotenza)
    player.roles = []
    player.roles.append(admin_role)
    db_session.add(player)
    db_session.commit()

    # Ricarica il giocatore per assicurarti che la sessione sia aggiornata
    db_session.refresh(player)
    assert player.is_admin is True

    return authenticated_client


# === Test sui Permessi ===
def test_permissions_not_logged_in(client: FlaskClient):
    routes_to_test = ["/players/", "/players/add", "/players/1", "/players/1/edit"]
    for route in routes_to_test:
        response_get = client.get(route)
        assert response_get.status_code == 302
        assert "auth/login" in response_get.headers["Location"]
    response_post = client.post("/players/1/delete")
    assert response_post.status_code == 302
    assert "auth/login" in response_post.headers["Location"]


def test_permissions_normal_user(authenticated_client: FlaskClient, sample_player):
    player_id = sample_player["player"].id
    # READ (OK)
    assert authenticated_client.get("/players/").status_code == 200
    assert authenticated_client.get(f"/players/{player_id}").status_code == 200
    # WRITE (Forbidden)
    assert authenticated_client.get("/players/add").status_code == 403
    # Un utente normale può modificare il proprio profilo
    assert authenticated_client.get(f"/players/{player_id}/edit").status_code == 200
    assert authenticated_client.post(f"/players/{player_id}/delete").status_code == 403


# === Test delle Rotte (come Admin) ===


class TestAdminPlayerRoutes:
    def test_admin_list_players(self, admin_client: FlaskClient, multiple_players):
        players = multiple_players(3)
        response = admin_client.get("/players/")
        assert response.status_code == 200
        assert b"Elenco Giocatori" in response.data
        assert bytes(players[0].nickname, "utf-8") in response.data

    def test_admin_list_db_error(self, admin_client: FlaskClient, mocker):
        # Copre views.py righe 70-71
        mocker.patch("app.db.session.scalars", side_effect=SQLAlchemyError("DB Error"))
        response = admin_client.get("/players/")
        assert response.status_code == 200
        # CORREZIONE: Messaggio Flash (HTML Encoded)
        assert b"Errore nel caricamento della lista dei giocatori." in response.data

    def test_admin_detail_player(self, admin_client: FlaskClient, sample_player):
        player = sample_player["player"]
        response = admin_client.get(f"/players/{player.id}")
        assert response.status_code == 200
        assert bytes(player.nickname, "utf-8") in response.data
        assert b"Statistiche" in response.data

    def test_admin_detail_404(self, admin_client: FlaskClient):
        response = admin_client.get("/players/99999")
        assert response.status_code == 404

    def test_admin_detail_db_error(
        self, admin_client: FlaskClient, sample_player, mocker
    ):
        # Copre views.py righe 166-167
        player_id = sample_player["player"].id

        mocker.patch(
            "app.routes.players.views.db.get_or_404",
            side_effect=SQLAlchemyError("DB Error"),
        )

        response = admin_client.get(f"/players/{player_id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"Elenco Giocatori" in response.data
        # CORREZIONE: Messaggio Flash (HTML Encoded)
        assert b"Errore nel caricamento dei dettagli del giocatore." in response.data

    def test_admin_add_player_get(self, admin_client: FlaskClient):
        response = admin_client.get("/players/add")
        assert response.status_code == 200
        assert b"Aggiungi Giocatore" in response.data
        assert b'name="old_password"' not in response.data

    def test_admin_add_player_post(self, admin_client: FlaskClient, db_session):
        form_data = {
            "nickname": "NuovoGiocatore",
            "email": "nuovo@test.com",
            "first_name": "Nome",
            "last_name": "Cognome",
            "password": "Valid_P@ssword1",
            "confirm_password": "Valid_P@ssword1",
        }
        response = admin_client.post(
            "/players/add", data=form_data, follow_redirects=True
        )
        assert response.status_code == 200

        player = db_session.query(Player).filter_by(email="nuovo@test.com").first()
        assert player is not None
        assert player.nickname == "NuovoGiocatore"
        assert len(player.roles) > 0

    def test_admin_add_player_fail_no_user_role(
        self, admin_client: FlaskClient, db_session, mocker
    ):
        # Copre views.py righe 123-125 (except SQLAlchemyError)
        mocker.patch("app.db.session.scalar", return_value=None)

        form_data = {
            "nickname": "Sfortunato",
            "email": "sfortunato@test.com",
            "first_name": "Nome",
            "last_name": "Cognome",
            "password": "Valid_P@ssword1",
            "confirm_password": "Valid_P@ssword1",
        }
        response = admin_client.post(
            "/players/add", data=form_data, follow_redirects=True
        )
        assert response.status_code == 200
        # CORREZIONE: Messaggio Flash (HTML Encoded)
        assert b"Errore interno: ruolo utente non trovato." in response.data
        player = db_session.query(Player).filter_by(email="sfortunato@test.com").first()
        assert player is None

    def test_admin_edit_player_get(self, admin_client: FlaskClient, sample_player):
        player = sample_player["player"]
        response = admin_client.get(f"/players/{player.id}/edit")
        assert response.status_code == 200
        assert b"Modifica Giocatore" in response.data or b"Modifica il tuo Profilo" in response.data
        assert f'value="{player.nickname}"'.encode("utf-8") in response.data
        assert b'name="old_password"' in response.data

    def test_admin_edit_player_post(
        self, admin_client: FlaskClient, sample_player, db_session
    ):
        """Testa la modifica (POST) di un giocatore (senza cambio password)."""
        player = sample_player["player"]
        original_email = player.email

        form_data = {
            "nickname": "NicknameModificato",
            "email": original_email,
            "first_name": "NomeModificato",
            "last_name": "CognomeModificato",
            "country": "IT",
            "old_password": "",
            "password": "",
            "confirm_password": "",
        }

        response = admin_client.post(
            f"/players/{player.id}/edit", data=form_data, follow_redirects=True
        )

        assert response.status_code == 200
        assert bytes(form_data["nickname"], "utf-8") in response.data

        db_session.refresh(player)
        assert player.nickname == "NicknameModificato"
        assert player.first_name == "NomeModificato"

    def test_admin_edit_player_db_error(
        self, admin_client: FlaskClient, sample_player, mocker
    ):
        # Copre views.py righe 248-255 (except SQLAlchemyError)
        player = sample_player["player"]

        mocker.patch(
            "app.db.session.commit", side_effect=SQLAlchemyError("DB Error on Edit")
        )

        form_data = {"nickname": "EditFail", "email": player.email}

        response = admin_client.post(
            f"/players/{player.id}/edit", data=form_data, follow_redirects=True
        )

        assert response.status_code == 200
        # --- CORREZIONE: Messaggio Flash (HTML Encoded per l'apostrofo) ---
        assert b"Errore durante l'" in response.data or b"Errore durante l&#39;" in response.data
        assert b"Modifica Giocatore" in response.data or b"Modifica il tuo Profilo" in response.data  # Resta sulla pagina di modifica

    def test_admin_delete_player(
        self, admin_client: FlaskClient, multiple_players, db_session
    ):
        """Testa l'eliminazione (POST) di un giocatore pulito."""
        player_to_delete = multiple_players(1)[0]
        player_id = player_to_delete.id

        response = admin_client.post(
            f"/players/{player_id}/delete", follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Elenco Giocatori" in response.data

        deleted_player = db_session.get(Player, player_id)
        assert deleted_player is None

    def test_admin_delete_player_with_participation(
        self,
        admin_client: FlaskClient,
        db_session,
        sample_player,
        create_tournament,
        add_participation,
        mocker,
    ):
        """
        Testa la logica di business chiave: NON si può eliminare un
        giocatore con partecipazioni.
        Copre views.py righe 296-301
        """
        player = sample_player["player"]
        player_id = player.id
        tournament = create_tournament(name="Torneo Reale")
        add_participation(player=player, tournament=tournament, posizione=1)

        # Simula l'IntegrityError (che viene catturato dalla view)
        mocker.patch(
            "app.db.session.delete",
            side_effect=IntegrityError("FK Constraint", "params", "orig"),
        )

        response = admin_client.post(
            f"/players/{player_id}/delete", follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Impossibile eliminare" in response.data
        assert b"Il giocatore ha partecipazioni ai tornei." in response.data

        player_exists = db_session.get(Player, player_id)
        assert player_exists is not None

    def test_admin_delete_player_db_error(
        self, admin_client: FlaskClient, multiple_players, mocker
    ):
        # Copre views.py righe 288-293 (except SQLAlchemyError)
        player = multiple_players(1)[0]

        # Simula un errore DB generico (diverso dall'IntegrityError)
        mocker.patch(
            "app.db.session.delete", side_effect=SQLAlchemyError("DB Error on Delete")
        )

        response = admin_client.post(
            f"/players/{player.id}/delete", follow_redirects=True
        )

        assert response.status_code == 200
        # --- CORREZIONE: Messaggio Flash (HTML Encoded per l'apostrofo) ---
        assert b"Errore durante l'eliminazione" in response.data or b"Errore durante l&#39;eliminazione" in response.data
        assert b"Elenco Giocatori" in response.data

    def test_admin_delete_player_csrf_fail(
        self, admin_client: FlaskClient, sample_player, mocker
    ):
        """
        Testa un fallimento CSRF (mockando il form).
        Copre views.py righe 304-306
        """
        mock_form_class = mocker.patch("app.routes.players.views.DeletePlayerForm")
        mock_form_instance = MagicMock()
        mock_form_instance.validate_on_submit.return_value = (
            False  # Simula fallimento CSRF
        )
        mock_form_class.return_value = mock_form_instance

        player_id = sample_player["player"].id

        # --- CORREZIONE: player_id.id -> player_id ---
        response = admin_client.post(
            f"/players/{player_id}/delete", follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Richiesta di eliminazione non valida o scaduta." in response.data
        assert b"Elenco Giocatori" in response.data


# === Test di Validazione Form (Copre forms.py 100%) ===


class TestPlayerAddValidation:
    """
    Testa i fallimenti di validazione per la rotta 'add_player'.
    Copre views.py righe 106-120
    """

    def test_add_post_validation_error(self, admin_client):
        # Copre views.py 106-117 (validate_on_submit == False)
        form_data = {"nickname": "", "email": "bad-email"}  # Nickname vuoto
        response = admin_client.post("/players/add", data=form_data)
        assert response.status_code == 200
        assert b"Aggiungi Giocatore" in response.data
        # Errore Form (UTF-8)
        assert b"Il nickname \xc3\xa8 obbligatorio." in response.data
        assert b"Formato email non valido." in response.data

    def test_add_post_password_required(self, admin_client):
        # Copre forms.py 139-141
        form_data = {
            "nickname": "testuser_new_2",
            "email": "testuser_new_2@test.com",
            "password": "",  # Errore: password vuota
            "confirm_password": "",
            "submit": "Salva Giocatore",
        }
        response = admin_client.post("/players/add", data=form_data)
        assert response.status_code == 200
        # Errore Form (UTF-8)
        assert (
            b"La password \xc3\xa8 obbligatoria per i nuovi giocatori." in response.data
        )

    def test_add_post_password_mismatch(self, admin_client):
        # Copre forms.py 146-147 (e anche EqualTo validator)
        form_data = {
            "nickname": "testuser_new",
            "email": "testuser_new@test.com",
            "password": "ValidPassword123",
            "confirm_password": "DIFFERENT",  # Errore: conferma diversa
            "submit": "Salva Giocatore",
        }
        response = admin_client.post("/players/add", data=form_data)
        assert response.status_code == 200
        assert b"Le nuove password devono corrispondere." in response.data


class TestPlayerEditValidation:
    """
    Testa i fallimenti di validazione per la rotta 'edit_player'.
    Copre views.py righe 176-191 e forms.py 152-176
    """

    def test_edit_post_validation_error(self, admin_client, sample_player):
        # Copre views.py 176-188 (validate_on_submit == False)
        player = sample_player["player"]
        form_data = {"nickname": "", "email": "bad-email"}  # Nickname vuoto
        response = admin_client.post(f"/players/{player.id}/edit", data=form_data)
        assert response.status_code == 200
        assert b"Modifica Giocatore" in response.data or b"Modifica il tuo Profilo" in response.data
        # Errore Form (UTF-8)
        assert b"Il nickname \xc3\xa8 obbligatorio." in response.data
        assert b"Formato email non valido." in response.data

    def test_edit_post_uniqueness_nickname(
        self, admin_client, sample_player, multiple_players
    ):
        # Copre forms.py riga 116
        p1 = sample_player["player"]
        p2 = multiple_players(1)[0]  # Un secondo giocatore

        form_data = {"nickname": p2.nickname, "email": p1.email}
        response = admin_client.post(f"/players/{p1.id}/edit", data=form_data)
        assert response.status_code == 200
        # Errore Form (UTF-8)
        assert b"Nickname gi\xc3\xa0 registrato." in response.data

    def test_edit_post_uniqueness_email(
        self, admin_client, sample_player, multiple_players
    ):
        # Copre forms.py riga 125
        p1 = sample_player["player"]
        p2 = multiple_players(1)[0]  # Un secondo giocatore

        form_data = {"nickname": p1.nickname, "email": p2.email}
        response = admin_client.post(f"/players/{p1.id}/edit", data=form_data)
        assert response.status_code == 200
        # Errore Form (UTF-8)
        assert b"Email gi\xc3\xa0 registrata." in response.data

    def test_edit_post_password_change_errors(
        self, admin_client, sample_player, db_session
    ):
        # Copre forms.py 152-154, 163-176
        player = sample_player["player"]
        correct_password = sample_player["password"]

        assert player.check_password(correct_password) is True

        base_data = {"nickname": player.nickname, "email": player.email}

        # 1. Errore: Nuova pass ma senza vecchia pass (righe 163-165)
        form_data = base_data.copy()
        form_data.update(
            {
                "old_password": "",  # Mancante
                "password": "NewValidPassword1",
                "confirm_password": "NewValidPassword1",
            }
        )
        response = admin_client.post(f"/players/{player.id}/edit", data=form_data)
        assert response.status_code == 200
        assert b"Devi inserire la password attuale" in response.data

        # 2. Errore: Vecchia pass sbagliata (righe 169-171)
        form_data = base_data.copy()
        form_data.update(
            {
                "old_password": "THIS_IS_WRONG",  # Sbagliata
                "password": "NewValidPassword1",
                "confirm_password": "NewValidPassword1",
            }
        )
        response = admin_client.post(f"/players/{player.id}/edit", data=form_data)
        assert response.status_code == 200
        # --- CORREZIONE: Aggiunto spazio ---
        assert b"Password attuale non corretta." in response.data

        # 3. Errore: Vecchia pass corretta, ma nuova pass mancante (righe 174-176)
        form_data = base_data.copy()
        form_data.update(
            {
                "old_password": correct_password,  # Corretta
                "password": "",  # Mancante
                "confirm_password": "",
            }
        )
        response = admin_client.post(f"/players/{player.id}/edit", data=form_data)
        assert response.status_code == 200
        assert b"Devi inserire la nuova password." in response.data

        # 4. Errore: Solo 'confirm_pwd' inserito (copre 152-154)
        # Il validatore 'EqualTo' scatta prima del nostro validatore custom
        form_data = base_data.copy()
        form_data.update(
            {
                "old_password": "",
                "password": "",
                "confirm_password": "SomePassword",  # Solo conferma
            }
        )
        response = admin_client.post(f"/players/{player.id}/edit", data=form_data)
        assert response.status_code == 200
        # --- CORREZIONE: Verifica l'errore corretto ---
        assert b"Le nuove password devono corrispondere." in response.data
