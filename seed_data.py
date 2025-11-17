import os
import json
import sys
import random
from dotenv import load_dotenv
from faker import Faker
from app_factory import create_app
from app import db
from app.models.player.base import Player
from app.models.tournament.base import Tournament
from app.models.tournament_player.base import TournamentPlayer
from datetime import datetime, timedelta
from decimal import Decimal
from app.models.roles import Role, create_default_roles

# Carica variabili d'ambiente (Serve per DATABASE_URL)
load_dotenv()

app = create_app()
fake = Faker(['it_IT'])  # Utilizziamo Faker per i dati demo

def _load_json_data(env_var_name: str, file_name: str) -> list:
    """
    Logica ibrida per caricare dati da Variabile d'Ambiente (PROD) o file JSON (DEV).
    """
    json_data = []
    
    # 1. Prova a caricare da Variabile d'Ambiente (es. Render)
    json_env_data = os.getenv(env_var_name)
    if json_env_data:
        print(f"🌍 Rilevato ambiente Cloud: Leggo '{env_var_name}' da variabile d'ambiente.")
        try:
            json_data = json.loads(json_env_data)
        except json.JSONDecodeError as e:
            print(f"❌ ERRORE CRITICO: Il JSON in '{env_var_name}' non è valido: {e}")
            sys.exit(1)
    
    # 2. Altrimenti, prova a caricare da file locale (es. PC Sviluppo)
    else:
        print(f"💻 Rilevato ambiente Locale: Cerco file '{file_name}'...")
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            print(f"✅ File '{file_name}' caricato con successo.")
        except FileNotFoundError:
            print(f"ℹ️  File '{file_name}' non trovato. Si procederà senza questi dati.")
        except json.JSONDecodeError as e:
            print(f"❌ ERRORE CRITICO: Il file JSON '{file_name}' non è valido: {e}")
            sys.exit(1)
            
    return json_data

def _populate_real_data(db_session, players_data: list, tournaments_data: list):
    """Popola il DB con i dati reali forniti dai file JSON/Env."""
    
    print("Popolamento con dati REALI...")
    
    # === 1. RUOLI ===
    admin_role = db_session.scalar(db.select(Role).filter_by(name="admin"))
    user_role = db_session.scalar(db.select(Role).filter_by(name="user"))

    # === 2. CREAZIONE PLAYERS ===
    # Dizionario per mappare "Nickname" -> Oggetto Player
    pmap = {}
    admin_player = None # L'admin principale per i tornei

    print(f"👤 Elaborazione di {len(players_data)} giocatori reali...")
    for p_data in players_data:
        existing = db_session.scalar(db.select(Player).filter_by(email=p_data['email']))
        
        if existing:
            player = existing
            player.password = p_data['password'] # Aggiorna la password se cambiata
        else:
            player = Player(
                first_name=p_data['first_name'],
                last_name=p_data['last_name'],
                nickname=p_data['nickname'],
                email=p_data['email'],
                country=p_data.get('country', 'IT')
            )
            player.password = p_data['password']
            db_session.add(player)
        
        # Assegnazione Ruoli
        if p_data.get('role') == 'admin':
            if admin_role not in player.roles:
                player.roles.append(admin_role)
            if admin_player is None: # Il primo admin trovato diventa admin dei tornei
                admin_player = player
        else:
            if user_role not in player.roles:
                player.roles.append(user_role)

        pmap[p_data['nickname']] = player

    db_session.commit()
    
    # Se nessun admin è stato specificato nei player, prendi il primo player
    if admin_player is None and pmap:
         admin_player = list(pmap.values())[0]

    print("✅ Giocatori reali salvati/aggiornati.")

    # === 3. CREAZIONE TORNEI ===
    print(f"🏆 Elaborazione di {len(tournaments_data)} tornei reali...")
    
    for t_data in tournaments_data:
        # Verifica duplicati
        existing_trn = db_session.scalar(db.select(Tournament).filter_by(name=t_data['name']))
        if existing_trn:
            continue # Salta il torneo se esiste già

        data_torneo = datetime.strptime(t_data['date'], "%Y-%m-%d").date()
        buy_in = Decimal(t_data['buy_in'])
        
        # Trova l'admin del torneo dal pmap
        trn_admin = pmap.get(t_data['admin_nickname'], admin_player) # Usa l'admin specificato o il default

        torneo = Tournament(
            name=t_data['name'],
            tournament_date=data_torneo,
            buy_in=buy_in,
            admin=trn_admin, 
        )
        db_session.add(torneo)
        db_session.flush()  # Ottiene l'ID del torneo prima del commit

        partecipanti = t_data['participants']
        
        for p_data in partecipanti:
            # Trova il player usando il nickname
            player = pmap.get(p_data['nickname'])
            if not player:
                print(f"⚠️  ATTENZIONE: Nickname '{p_data['nickname']}' non trovato nel file players. Saltato.")
                continue

            tp = TournamentPlayer(
                tournament_id=torneo.id,
                player_id=player.id,
                rebuy=p_data['rebuy'],
                posizione=p_data['position'],
                prize=Decimal(p_data['prize']),
                rebuy_total_spent=Decimal(p_data['rebuy_total_spent'])
            )
            db_session.add(tp)

        # Calcola il prize pool totale
        total_buy_in = buy_in * len(partecipanti)
        total_rebuy_spent = sum(Decimal(p['rebuy_total_spent']) for p in partecipanti)
        torneo.prize_pool = total_buy_in + total_rebuy_spent

    db_session.commit()
    print("✅ Tornei reali salvati.")


def _generate_dummy_data(db_session):
    """Popola il DB con dati DEMO (Faker) se non trova file privati."""
    
    print("Popolamento con dati DEMO (Faker)...")

    # === 1. RUOLI ===
    admin_role = db_session.scalar(db.select(Role).filter_by(name="admin"))
    user_role = db_session.scalar(db.select(Role).filter_by(name="user"))
    
    # === 2. CREAZIONE PLAYERS DEMO ===
    players_demo = []
    
    # Admin Demo
    admin_demo = Player(
        first_name="Admin",
        last_name="Demo",
        nickname="AdminDemo",
        email="admin@demo.com",
        country="IT"
    )
    admin_demo.password = "password123" # Password sicura per demo
    admin_demo.roles.append(admin_role)
    db_session.add(admin_demo)
    players_demo.append(admin_demo)
    
    # Utenti Demo
    for i in range(10):
        first_name = fake.first_name()
        player = Player(
            first_name=first_name,
            last_name=fake.last_name(),
            nickname=f"{first_name}{i}",
            email=fake.email(),
            country=fake.country_code()
        )
        player.password = "password123"
        player.roles.append(user_role)
        db_session.add(player)
        players_demo.append(player)
        
    db_session.commit()
    print(f"👤 Creati {len(players_demo)} giocatori demo.")

    # === 3. CREAZIONE TORNEI DEMO ===
    for i in range(5):
        buy_in = Decimal(random.choice([10, 20, 50]))
        data_torneo = datetime.now().date() - timedelta(days=random.randint(5, 50))
        
        torneo = Tournament(
            name=f"Demo Tournament #{i+1}",
            tournament_date=data_torneo,
            buy_in=buy_in,
            admin=admin_demo
        )
        db_session.add(torneo)
        db_session.flush()
        
        # Seleziona partecipanti random
        num_partecipanti = random.randint(4, len(players_demo))
        partecipanti_demo = random.sample(players_demo, num_partecipanti)
        
        # Calcolo montepremi fittizio
        total_prize_pool = buy_in * num_partecipanti
        rebuys_totali = 0
        
        posizioni = list(range(1, num_partecipanti + 1))
        random.shuffle(posizioni)
        
        # Assegna premi (es. 50/30/20)
        prizes = [
            round(total_prize_pool * Decimal(0.5), 2),
            round(total_prize_pool * Decimal(0.3), 2),
            round(total_prize_pool * Decimal(0.2), 2)
        ]

        for idx, player in enumerate(partecipanti_demo):
            posizione = posizioni[idx]
            prize = Decimal("0.00")
            
            if posizione == 1:
                prize = prizes[0]
            elif posizione == 2:
                prize = prizes[1]
            elif posizione == 3:
                prize = prizes[2]
                
            rebuy = random.randint(0, 3)
            rebuy_total_spent = Decimal(rebuy) * buy_in
            rebuys_totali += rebuy_total_spent

            tp = TournamentPlayer(
                tournament_id=torneo.id,
                player_id=player.id,
                rebuy=rebuy,
                posizione=posizione if posizione <= 3 else None, # Solo i primi 3 a premio
                prize=prize,
                rebuy_total_spent=rebuy_total_spent
            )
            db_session.add(tp)
        
        torneo.prize_pool = total_prize_pool + rebuys_totali
    
    db_session.commit()
    print(f"🏆 Creati 5 tornei demo.")
    

def populate():
    with app.app_context():
        # Scommenta queste righe se vuoi pulire il DB ogni volta che lanci il seed
        # db.session.remove()
        # db.drop_all()
        # db.create_all()

        print("🛠  Avvio procedura di popolamento database...")
        
        # === 1. CREA RUOLI (Sempre) ===
        create_default_roles()

        # === 2. CARICA DATI PRIVATI ===
        players_data = _load_json_data("PLAYERS_DATA_JSON", "private_data.json")
        tournaments_data = _load_json_data("TOURNAMENTS_DATA_JSON", "tournaments.json")

        # === 3. DECIDI SE USARE DATI REALI O DEMO ===
        # Controlliamo solo i player, assumendo che se ci sono i player, 
        # ci debbano essere anche i tornei.
        if players_data:
            _populate_real_data(db.session, players_data, tournaments_data)
        else:
            print("Nessun dato privato (file/env) trovato.")
            _generate_dummy_data(db.session)

        print("✅ Database popolato con successo!")

if __name__ == "__main__":
    populate()