import pytest
from flask.testing import FlaskClient
from sqlalchemy.exc import OperationalError
from app import db
from app.models.player import Player


def test_login_get_page(client: FlaskClient):
    """
    Testa il caricamento (GET) della pagina di login.
    (Coverage: righe 31, 104)
    """
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Accedi" in response.data
    assert b"Email" in response.data
    assert b"Password" in response.data


def test_login_page_when_already_authenticated(authenticated_client: FlaskClient):
    """
    Testa che un utente già loggato venga reindirizzato.
    (Coverage: righe 27-29)
    """
    response = authenticated_client.get("/auth/login", follow_redirects=True)

    assert response.status_code == 200
    assert b"Sei gi\xc3\xa0 autenticato." in response.data
    assert b"Dashboard" in response.data  # Reindirizzato alla main.index


def test_login_with_valid_credentials(client: FlaskClient, sample_player: dict):
    """
    Testa un login standard corretto (senza 'next' param).
    (Coverage: righe 33-52, 62-65, 77)
    """
    # --- CORREZIONE BUG TEST ---
    # Il test non ha bisogno di chiamare url_for.
    # Eseguiamo semplicemente la richiesta.
    with client:
        response = client.post(
            "/auth/login",
            data={
                "email": sample_player["email"],
                "password": sample_player["password"],
                "submit": "Accedi",
            },
            follow_redirects=True,
        )  # Segui il redirect

        assert response.status_code == 200
        # Ora che i bug nel views.py sono corretti, questo passerà
        assert b"Bentornato, " in response.data
        assert b"Dashboard" in response.data
    # --- FINE CORREZIONE ---


def test_login_with_safe_next_redirect(client: FlaskClient, sample_player: dict):
    """
    Testa che il login reindirizzi correttamente a un URL 'next' sicuro.
    (Coverage: righe 67-71)
    """
    response = client.post(
        "/auth/login?next=/players/",
        data={
            "email": sample_player["email"],
            "password": sample_player["password"],
            "submit": "Accedi",
        },
        follow_redirects=False,
    )  # NON seguire il redirect

    # La view (ora corretta) rileva un URL sicuro e reindirizza a '/players/'
    assert response.status_code == 302
    assert response.headers["Location"] == "/players/"


def test_login_with_unsafe_next_redirect(
    client: FlaskClient, sample_player: dict, mocker
):
    """
    Testa che il login ignori un URL 'next' non sicuro.
    (Coverage: righe 73-75)
    """
    # Mock del logger per verificare che l'avviso venga registrato
    mock_warn = mocker.patch("app.routes.auth.views.log.warning")

    response = client.post(
        "/auth/login?next=http://evil-site.com",
        data={
            "email": sample_player["email"],
            "password": sample_player["password"],
            "submit": "Accedi",
        },
        follow_redirects=False,
    )

    # La view (ora corretta) rileva un URL non sicuro e reindirizza a '/'
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    # Verifica che il warning sia stato loggato
    mock_warn.assert_called_once_with(
        "Unsafe 'next' URL detected: http://evil-site.com. Redirecting to index."
    )


def test_login_with_empty_next_redirect(client: FlaskClient, sample_player: dict):
    """
    Testa che il login con 'next=' reindirizzi a '/'.
    (Coverage: righe 67 e 77)
    """
    response = client.post(
        "/auth/login?next=",
        data={
            "email": sample_player["email"],
            "password": sample_player["password"],
            "submit": "Accedi",
        },
        follow_redirects=False,
    )

    # La view rileva 'next' vuoto, lo considera non sicuro, e reindirizza a '/'
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_login_invalid_credentials(client: FlaskClient, sample_player: dict):
    """
    Testa un tentativo di login con password errata.
    (Coverage: righe 81-84)
    """
    response = client.post(
        "/auth/login",
        data={
            "email": sample_player["email"],
            "password": "wrong_password",
            "submit": "Accedi",
        },
    )

    # La vista (ora corretta) restituisce 401
    assert response.status_code == 401
    assert b"Login non riuscito. Controlla email e password." in response.data
    assert b"Bentornato" not in response.data


def test_login_audit_update_fails(client: FlaskClient, sample_player: dict, mocker):
    """
    Testa che il login abbia successo anche se l'audit (commit) fallisce.
    (Coverage: righe 53-58)
    """
    mocker.patch(
        "app.db.session.commit",
        side_effect=OperationalError("Simulated DB Error", {}, {}),
    )
    mock_rollback = mocker.patch("app.db.session.rollback")

    with client:
        response_post = client.post(
            "/auth/login",
            data={
                "email": sample_player["email"],
                "password": sample_player["password"],
                "submit": "Accedi",
            },
        )

        assert response_post.status_code == 302
        assert response_post.headers["Location"] == "/"

        response_get = client.get(response_post.headers["Location"])

        assert response_get.status_code == 200
        # Il messaggio flash "Bentornato" DEVE essere presente
        assert b"Bentornato, " in response_get.data
        mock_rollback.assert_called_once()


def test_login_unexpected_exception(client: FlaskClient, sample_player: dict, mocker):
    """
    Testa il blocco 'except' generico (es. DB offline).
    (Coverage: righe 86-98)
    """
    mocker.patch(
        "app.db.session.scalar", side_effect=Exception("Simulated unexpected error")
    )
    mock_rollback = mocker.patch("app.db.session.rollback")

    with client:
        response_post = client.post(
            "/auth/login",
            data={
                "email": sample_player["email"],
                "password": sample_player["password"],
                "submit": "Accedi",
            },
        )

        # L'eccezione (ora corretta) è catturata e ricarica la pagina con 500
        assert response_post.status_code == 500
        assert (
            b"Si \xc3\xa8 verificato un errore durante il login." in response_post.data
        )
        mock_rollback.assert_called_once()


def test_logout(authenticated_client: FlaskClient):
    """
    Testa la funzione di logout.
    (Coverage: righe 109-114)
    """
    response = authenticated_client.get("/auth/logout", follow_redirects=True)

    assert response.status_code == 200
    assert b"Sei stato disconnesso con successo." in response.data
    assert b"Dashboard" in response.data
    assert b'href="/players/profile/' not in response.data
