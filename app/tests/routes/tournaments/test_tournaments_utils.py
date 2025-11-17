import pytest
from flask.testing import FlaskClient
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import MagicMock, patch

# Importa i modelli e il db necessari
from app.models import Player, Role, Tournament
from app import db


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
    db_session.commit()

    # 2. Assegna il ruolo admin al sample_player
    player = sample_player["player"]
    if admin_role not in player.roles:
        player.roles.append(admin_role)
        db_session.add(player)
        db_session.commit()

    db_session.refresh(player)
    return authenticated_client


# === Test di Coverage per Errori DB e Eccezioni ===


class TestTournamentErrorCoverage:
    """
    Questa classe testa specificamente i blocchi 'except'
    mancanti in app/routes/tournaments/views.py.
    """

    def test_get_player_choices_db_error(self, admin_client: FlaskClient, mocker):
        # Copre views.py righe 38-40
        mocker.patch("app.db.session.scalars", side_effect=SQLAlchemyError("DB Error"))

        response = admin_client.get("/tournaments/add")
        assert response.status_code == 200
        assert b"--- Errore Caricamento ---" in response.data

    def test_add_tournament_db_error(
        self, admin_client: FlaskClient, mocker, multiple_players
    ):
        # Copre views.py riga 118 (except SQLAlchemyError -> handle_db_error)

        p1 = multiple_players(1)[0]

        mocker.patch(
            "app.db.session.commit", side_effect=SQLAlchemyError("DB Commit Error")
        )

        form_data = {
            "name": "Torneo DB Error",
            "tournament_date": "2025-01-01",
            "buy_in": "100",
            "participants-0-player_id": str(p1.id),
        }

        response = admin_client.post(
            "/tournaments/add", data=form_data, follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Aggiungi Torneo" in response.data
        # --- CORREZIONE: Messaggio Flash (UTF-8 Bytes) ---
        assert b"Si \xc3\xa8 verificato un errore nel database" in response.data

    def test_add_tournament_generic_error(self, admin_client: FlaskClient, mocker):
        # Copre views.py righe 120-121 (except Exception -> handle_db_error)
        mocker.patch("app.db.session.flush", side_effect=Exception("Generic Error"))

        form_data = {
            "name": "Torneo Generic Error",
            "tournament_date": "2025-01-01",
            "buy_in": "100",
        }

        response = admin_client.post(
            "/tournaments/add", data=form_data, follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Aggiungi Torneo" in response.data
        # --- CORREZIONE: Messaggio Flash (UTF-8 Bytes) ---
        assert b"Si \xc3\xa8 verificato un errore nel database" in response.data

    def test_edit_tournament_db_error(
        self, admin_client: FlaskClient, create_tournament, mocker
    ):
        # Copre views.py riga 252 (except SQLAlchemyError -> handle_db_error)
        t = create_tournament()
        mocker.patch(
            "app.db.session.commit", side_effect=SQLAlchemyError("DB Commit Error")
        )

        form_data = {
            "name": "Edit DB Error",
            "tournament_date": t.tournament_date.isoformat(),
            "buy_in": t.buy_in,
        }

        response = admin_client.post(
            f"/tournaments/{t.id}/edit", data=form_data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Modifica Torneo" in response.data
        # --- CORREZIONE: Messaggio Flash (UTF-8 Bytes) ---
        assert b"Si \xc3\xa8 verificato un errore nel database" in response.data

    def test_edit_tournament_generic_error(
        self, admin_client: FlaskClient, create_tournament, mocker
    ):
        # Copre views.py righe 254-255 (except Exception -> handle_db_error)
        t = create_tournament()

        mock_scalar_result = MagicMock()
        mock_scalar_result.all.return_value = []
        mocker.patch(
            "app.db.session.scalars",
            side_effect=[mock_scalar_result, Exception("Generic Error")],
        )

        form_data = {
            "name": "Edit Generic Error",
            "tournament_date": t.tournament_date.isoformat(),
            "buy_in": t.buy_in,
        }

        response = admin_client.post(
            f"/tournaments/{t.id}/edit", data=form_data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Modifica Torneo" in response.data
        # --- CORREZIONE: Messaggio Flash (UTF-8 Bytes) ---
        assert b"Si \xc3\xa8 verificato un errore nel database" in response.data

    def test_delete_tournament_db_error(
        self, admin_client: FlaskClient, create_tournament, mocker
    ):
        # Copre views.py righe 285-286 (except SQLAlchemyError -> handle_db_error)
        t = create_tournament()
        mocker.patch(
            "app.db.session.delete", side_effect=SQLAlchemyError("DB Delete Error")
        )

        response = admin_client.post(
            f"/tournaments/{t.id}/delete", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Elenco Tornei" in response.data
        # --- CORREZIONE: Messaggio Flash (UTF-8 Bytes) ---
        assert b"Si \xc3\xa8 verificato un errore nel database" in response.data

    def test_delete_tournament_csrf_fail(
        self, admin_client: FlaskClient, create_tournament, mocker
    ):
        # Copre views.py righe 288-291 (else -> form fail)
        t = create_tournament()

        mock_form_class = mocker.patch(
            "app.routes.tournaments.views.DeleteTournamentForm"
        )
        mock_form_instance = MagicMock()
        mock_form_instance.validate_on_submit.return_value = False
        mock_form_class.return_value = mock_form_instance

        response = admin_client.post(
            f"/tournaments/{t.id}/delete", follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Elenco Tornei" in response.data
        # Questo messaggio (senza caratteri speciali) è corretto
        assert b"Richiesta di eliminazione non valida o scaduta." in response.data

    def test_detail_tournament_db_error(
        self, admin_client: FlaskClient, create_tournament, mocker
    ):
        # Copre views.py righe 326-328 (except SQLAlchemyError -> handle_db_error)
        t = create_tournament()

        mocker.patch(
            "app.db.session.scalar", side_effect=SQLAlchemyError("DB Detail Error")
        )

        response = admin_client.get(f"/tournaments/{t.id}", follow_redirects=True)

        assert response.status_code == 200
        assert b"Elenco Tornei" in response.data
        # --- CORREZIONE: Messaggio Flash (UTF-8 Bytes) ---
        assert b"Si \xc3\xa8 verificato un errore nel database" in response.data
