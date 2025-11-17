import pytest
import uuid
import sys
import os
from datetime import date
from decimal import Decimal

# --- Correzione del Path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import principali ---
from app_factory import create_app, db as _db  # Rinomina db per evitare conflitti
from app.models import Player, Tournament, TournamentPlayer, Role


# --- Fixture per App (scope 'session') ---
@pytest.fixture(scope="session")
def app():
    """
    Fixture che crea un'istanza dell'app Flask per l'intera sessione di test.
    """
    app_instance = create_app(is_testing=True)
    with app_instance.app_context():
        yield app_instance


# --- NUOVA GESTIONE DATABASE PER TEST DI INTEGRAZIONE ---


@pytest.fixture(scope="session")
def db(app):
    """
    Fixture 'db' (scope sessione) che inizializza il database una volta.
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()
        _db.session.remove()


@pytest.fixture(scope="function")
def db_session(db, app):
    """
    Fixture 'db_session' (scope funzione) per l'isolamento dei test.

    Questa è la correzione cruciale:
    Cancella TUTTI i dati da TUTTE le tabelle dopo ogni test.
    Questo previene che i dati di un test (es. auth) finiscano
    in un altro test (es. main).
    """
    with app.app_context():
        yield _db.session

        # --- PULIZIA OBBLIGATORIA DOPO OGNI TEST ---
        # Rimuovi la sessione per rilasciare i lock
        _db.session.remove()

        # Cancella i dati da tutte le tabelle
        # (Usa .execute() per comandi SQL raw se necessario per TRUNCATE)
        # Per SQLite, delete funziona

        # Inverti l'ordine per rispettare i Foreign Keys
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


# --- Fixture Client (usano db_session) ---


@pytest.fixture(scope="function")
def client(app, db_session):
    """
    Fixture per ottenere un client di test Flask pulito e NON autenticato.
    'db_session' è incluso per garantire che il DB sia pulito prima dell'uso.
    """
    return app.test_client()


@pytest.fixture
def sample_player(db_session):
    """
    Crea e salva un giocatore di esempio con una password nel DB di test.
    """
    from app_factory import bcrypt

    unique_nickname = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{unique_nickname}@test.com"
    password = "Valid_P@ssword1"  # Password valida

    player = Player(
        first_name="Test",
        last_name="User",
        nickname=unique_nickname,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
    )
    db_session.add(player)
    db_session.commit()

    return {"player": player, "email": email, "password": password}


@pytest.fixture
def sample_tournament(db_session, sample_player):  # Aggiunta dipendenza sample_player
    """Crea e salva un torneo di esempio nel DB di test."""
    admin = sample_player["player"]  # Un torneo ora richiede un admin

    tournament = Tournament(
        name="Test Tournament",
        prize_pool=Decimal("1000.00"),
        tournament_date=date.today(),
        buy_in=Decimal("100.00"),
        admin_id=admin.id,  # CORREZIONE: admin_id è obbligatorio
    )
    db_session.add(tournament)
    db_session.commit()
    return tournament


@pytest.fixture
def authenticated_client(app, db_session, sample_player):
    """
    Restituisce un client di test NUOVO e GIÀ AUTENTICATO.
    """
    auth_client = app.test_client()

    auth_client.post(
        "/auth/login",
        data={
            "email": sample_player["email"],
            "password": sample_player["password"],
            "submit": "Accedi",
        },
        follow_redirects=True,
    )

    return auth_client


# --- Factory Fixtures (per creare dati complessi) ---


@pytest.fixture
def create_tournament(db_session, sample_player):  # Aggiunta dipendenza sample_player
    """Factory fixture per creare tornei con parametri personalizzati."""

    default_admin = sample_player["player"]

    def _create_tournament(
        name="T1",
        buy_in=Decimal("100.00"),
        tournament_date=None,
        prize_pool=None,
        admin_id=None,  # Permetti override
    ):
        tournament = Tournament(
            name=name,
            tournament_date=tournament_date or date.today(),
            buy_in=buy_in,
            prize_pool=prize_pool,
            admin_id=admin_id or default_admin.id,  # CORREZIONE
        )
        db_session.add(tournament)
        db_session.commit()
        return tournament

    return _create_tournament


@pytest.fixture
def add_participation(db_session):
    """Factory fixture per aggiungere una partecipazione a un torneo."""

    def _add_participation(
        player, tournament, prize=None, rebuy=0, posizione=None, rebuy_total_spent=None
    ):
        if rebuy_total_spent is None:
            buy_in = tournament.buy_in or Decimal("0.00")
            rebuy_total_spent_calc = buy_in * Decimal(rebuy)
        else:
            rebuy_total_spent_calc = Decimal(str(rebuy_total_spent))

        tp = TournamentPlayer(
            player_id=player.id,
            tournament_id=tournament.id,
            prize=prize,
            rebuy=rebuy,
            rebuy_total_spent=rebuy_total_spent_calc,
            posizione=posizione,
        )
        db_session.add(tp)
        db_session.commit()
        return tp

    return _add_participation


@pytest.fixture
def multiple_players(db_session):
    """Factory fixture per creare N giocatori di esempio."""

    def _create_multiple(n=3):
        players = []
        for i in range(n):
            nickname = f"testuser_{uuid.uuid4().hex[:8]}"
            player = Player(
                first_name="Test",
                last_name="User",
                nickname=nickname,
                email=f"{nickname}@test.com",
                password_hash="placeholder_hash",
            )
            db_session.add(player)
            players.append(player)

        db_session.commit()
        for p in players:
            db_session.refresh(p)
        return players

    return _create_multiple
