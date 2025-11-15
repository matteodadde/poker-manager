import os
import json
import sys
from dotenv import load_dotenv
from app_factory import create_app
from app import db
from app.models.player.base import Player
from app.models.tournament.base import Tournament
from app.models.tournament_player.base import TournamentPlayer
from datetime import datetime
from decimal import Decimal
from app.models.roles import Role, create_default_roles

# Carica variabili d'ambiente (Serve per DATABASE_URL, non più per le password user)
load_dotenv()

app = create_app()

def populate():
    with app.app_context():
        # Scommenta queste righe se vuoi pulire il DB ogni volta che lanci il seed
        # db.drop_all()
        # db.create_all()

        # === 1. CARICAMENTO DATI (Logica Ibrida: Locale vs Cloud) ===
        print("🛠  Avvio procedura di popolamento database...")
        players_data = []
        
        # A. Cerchiamo la variabile d'ambiente (Per RENDER)
        json_env_data = os.getenv("PLAYERS_DATA_JSON")

        if json_env_data:
            print("🌍 Rilevato ambiente Cloud: Leggo dati da variabile d'ambiente.")
            try:
                players_data = json.loads(json_env_data)
            except json.JSONDecodeError as e:
                print(f"❌ ERRORE CRITICO: Il JSON nella variabile d'ambiente non è valido: {e}")
                sys.exit(1)
        
        # B. Altrimenti cerchiamo il file locale (Per il tuo PC)
        else:
            print("💻 Rilevato ambiente Locale: Cerco file 'private_data.json'...")
            try:
                with open('private_data.json', 'r', encoding='utf-8') as f:
                    players_data = json.load(f)
            except FileNotFoundError:
                print("\n❌ ERRORE: Nessuna fonte dati trovata!")
                print("1. In LOCALE: Assicurati che esista il file 'private_data.json'.")
                print("2. Su RENDER: Incolla il contenuto del JSON nella variabile 'PLAYERS_DATA_JSON'.")
                sys.exit(1)

        # === 2. RUOLI ===
        create_default_roles()
        admin_role = db.session.scalar(db.select(Role).filter_by(name="admin"))
        user_role = db.session.scalar(db.select(Role).filter_by(name="user"))

        # === 3. CREAZIONE PLAYERS ===
        # Dizionario per mappare "Nickname" -> Oggetto Player
        # Questo serve per poter usare le variabili (dadde, gigi) nella sezione tornei
        pmap = {}

        print(f"👤 Elaborazione di {len(players_data)} giocatori...")

        for p_data in players_data:
            # Controlla se esiste già per evitare errori di duplicati
            existing = db.session.scalar(db.select(Player).filter_by(email=p_data['email']))
            
            if existing:
                player = existing
                # Aggiorniamo la password se è cambiata nel JSON
                player.password = p_data['password']
            else:
                player = Player(
                    first_name=p_data['first_name'],
                    last_name=p_data['last_name'],
                    nickname=p_data['nickname'],
                    email=p_data['email'],
                    country=p_data.get('country', 'IT')
                )
                player.password = p_data['password']
                db.session.add(player)
            
            # Assegnazione Ruoli
            if p_data.get('role') == 'admin':
                if admin_role not in player.roles:
                    player.roles.append(admin_role)
            else:
                if user_role not in player.roles:
                    player.roles.append(user_role)

            # Salviamo il player nella mappa usando il nickname come chiave
            pmap[p_data['nickname']] = player

        db.session.commit()
        print("✅ Giocatori salvati/aggiornati.")

        # === 4. MAPPATURA VARIABILI PER COMPATIBILITÀ ===
        # Qui assegniamo le variabili che usi nello storico tornei agli oggetti reali del DB.
        # Se nel JSON cambi un nickname, devi aggiornarlo anche qui!
        try:
            dadde = pmap["Dadde"]
            gigi = pmap["Gigi"]
            bulle = pmap["Bulle"]
            fili = pmap["Fili"]
            andre = pmap["Andre"]
            spado = pmap["Spado"]
            tommy = pmap["Tommy"]
            matte = pmap["Matte"]
            dario = pmap["Dario"]
            pippi = pmap["Pippi"]
            cri = pmap["Cri"]
            poltro = pmap["Poltro"]
            gero = pmap["Gero"]
            raffa = pmap["Raffa"]
            pilo = pmap["Pilo"]
        except KeyError as e:
            print(f"❌ ERRORE: Nel file JSON manca il giocatore con nickname: {e}")
            print("Controlla che il 'nickname' nel JSON corrisponda esattamente alla variabile usata nello script.")
            sys.exit(1)

        # === 5. TORNEI ===
        # (Questa sezione rimane identica al tuo file originale, 
        # ora le variabili 'dadde', 'gigi' ecc. sono popolate correttamente)
        
        tornei = [
            ("Torneo 1", "2025-05-08", 10, [
                (dadde, 0, 2, "30.00", "0.00"),
                (gigi, 1, None, "0.00", "10.00"),
                (bulle, 0, 1, "70.00", "0.00"),
                (fili, 6, 3, "10.00", "60.00"),
            ]),
            ("Torneo 2", "2025-05-09", 10, [
                (gigi, 0, 3, "25.00", "0.00"),
                (andre, 0, None, "0.00", "0.00"),
                (bulle, 0, 2, "30.00", "0.00"),
                (spado, 1, None, "0.00", "10.00"),
                (tommy, 1, None, "0.00", "10.00"),
                (matte, 0, 4, "20.00", "0.00"),
                (dario, 0, None, "0.00", "0.00"),
                (fili, 0, 1, "55.00", "0.00"),
                (pippi, 2, None, "0.00", "20.00"),
            ]),
            ("Torneo 3", "2025-05-13", 10, [
                (fili, 3, None, "0.00", "30.00"),
                (pippi, 0, 1, "55.00", "0.00"),
                (dadde, 0, 2, "25.00", "0.00"),
                (gigi, 1, None, "0.00", "10.00"),
            ]),
            ("Torneo 4", "2025-05-13", 10, [
                (fili, 0, None, "0.00", "0.00"),
                (pippi, 0, 1, "40.00", "0.00"),
                (dadde, 0, None, "0.00", "0.00"),
                (gigi, 0, None, "0.00", "0.00"),
            ]),
            ("Torneo 5", "2025-05-15", 10, [
                (fili, 8, 3, "20.00", "80.00"),
                (pippi, 1, None, "0.00", "10.00"),
                (dadde, 1, 1, "100.00", "10.00"),
                (gigi, 0, None, "0.00", "0.00"),
                (bulle, 0, 2, "50.00", "0.00"),
                (cri, 1, None, "0.00", "10.00"),
            ]),
            ("Torneo 6", "2025-05-17", 10, [
                (fili, 1, None, "0.00", "10.00"),
                (pippi, 0, 1, "75.00", "0.00"),
                (dadde, 0, None, "0.00", "0.00"),
                (gigi, 0, 2, "35.00", "0.00"),
                (bulle, 0, 3, "10.00", "0.00"),
                (cri, 5, None, "0.00", "50.00"),
            ]),
            ("Torneo 7 (Spin & Go)", "2025-05-17", 10, [
                (pippi, 0, None, "0.00", "0.00"),
                (cri, 0, None, "0.00", "0.00"),
                (gigi, 0, 1, "30.00", "0.00"),
            ]),
            ("Torneo 8", "2025-05-18", 10, [
                (gigi, 0, None, "0.00", "0.00"),
                (dario, 0, None, "0.00", "0.00"),
                (tommy, 0, 2, "20.00", "0.00"),
                (pippi, 0, 1, "60.00", "0.00"),
                (cri, 1, None, "0.00", "10.00"),
                (fili, 1, None, "0.00", "10.00"),
            ]),
            ("Torneo 9", "2025-05-22", 10, [
                (bulle, 0, 2, "35.00", "0.00"),
                (pippi, 4, 1, "75.00", "40.00"),
                (fili, 2, None, "0.00", "20.00"),
                (dadde, 0, 3, "10.00", "0.00"),
                (gigi, 1, None, "0.00", "10.00"),
            ]),
            ("Torneo 10", "2025-05-29", 10, [
                (bulle, 1, None, "0.00", "10.00"),
                (fili, 0, 1, "40.00", "0.00"),
                (pippi, 1, None, "0.00", "10.00"),
                (gigi, 0, 2, "20.00", "0.00"),
            ]),
            ("Torneo 11", "2025-05-31", 10, [
                (pippi, 2, 2, "25.00", "20.00"),
                (fili, 2, None, "0.00", "20.00"),
                (bulle, 0, 1, "55.00", "0.00"),
                (gigi, 0, None, "0.00", "0.00"),
            ]),
            ("Torneo 12", "2025-06-06", 10, [
                (gero, 1, None, "0.00", "10.00"),
                (pippi, 0, 1, "50.00", "0.00"),
                (fili, 0, None, "0.00", "0.00"),
                (dadde, 0, None, "0.00", "0.00"),
                (gigi, 0, 2, "20.00", "0.00"),
                (bulle, 0, None, "0.00", "0.00"),
            ]),
            ("Torneo 13", "2025-06-09", 10, [
                (dadde, 2, 3, "10.00", "20.00"),
                (pippi, 3, 2, "60.00", "30.00"),
                (fili, 7, 4, "10.00", "70.00"),
                (gigi, 0, 1, "110.00", "0.00"),
                (gero, 2, None, "0.00", "20.00"),
            ]),
            ("Torneo 14", "2025-06-10", 10, [
                (pippi, 4, None, "0.00", "40.00"),
                (gigi, 0, 1, "100.00", "0.00"),
                (dadde, 0, 3, "20.00", "0.00"),
                (gero, 2, 2, "50.00", "20.00"),
                (fili, 6, None, "0.00", "60.00"),
            ]),
            ("Torneo 15", "2025-06-11", 10, [
                (gigi, 0, 1, "40.00", "0.00"),
                (bulle, 0, None, "0.00", "0.00"),
                (fili, 2, None, "0.00", "20.00"),
                (cri, 0, 2, "20.00", "0.00"),
            ]),
            ("Torneo 16", "2025-06-12", 10, [
                (gigi, 0, 3, "20.00", "0.00"),
                (andre, 1, None, "0.00", "10.00"),
                (bulle, 0, None, "0.00", "0.00"),
                (cri, 3, 1, "120.00", "30.00"),
                (pippi, 3, 2, "60.00", "30.00"),
                (gero, 3, None, "0.00", "30.00"),
                (fili, 3, None, "0.00", "30.00"),
            ]),
            ("Torneo 17", "2025-06-15", 10, [
                (fili, 1, 1, "60.00", "10.00"),
                (gigi, 1, None, "0.00", "10.00"),
                (pippi, 2, None, "0.00", "20.00"),
                (dadde, 1, 2, "30.00", "10.00"),
            ]),
            ("Torneo 18", "2025-06-18", 10, [
                (fili, 10, None, "0.00", "100.00"),
                (dadde, 0, 2, "60.00", "0.00"),
                (gigi, 1, None, "0.00", "10.00"),
                (gero, 0, 1, "110.00", "0.00"),
                (pippi, 3, 3, "20.00", "30.00"),
            ]),
            ("Torneo 19", "2025-06-27", 10, [
                (fili, 4, None, "0.00", "40.00"),
                (dadde, 1, None, "0.00", "10.00"),
                (gigi, 0, 1, "70.00", "0.00"),
                (pippi, 1, 2, "30.00", "10.00"),
            ]),
            ("Torneo 20", "2025-07-05", 10, [
                (dario, 0, 1, "70.00", "0.00"),
                (gigi, 2, None, "0.00", "20.00"),
                (dadde, 2, 2, "30.00", "20.00"),
                (matte, 0, None, "0.00", "0.00"),
                (tommy, 1, 3, "0.00", "10.00"),
            ]),
            ("Torneo 21", "2025-07-15", 10, [
                (fili, 5, 3, "20.00", "50.00"),
                (gigi, 1, None, "0.00", "10.00"),
                (pippi, 0, 2, "40.00", "0.00"),
                (dadde, 0, 1, "100.00", "0.00"),
                (raffa, 5, None, "0.00", "50.00"),
            ]),
            ("Torneo 22", "2025-07-22", 10, [
                (fili, 7, None, "0.00", "70.00"),
                (gigi, 0, 2, "40.00", "0.00"),
                (pippi, 1, 1, "90.00", "10.00"),
                (dadde, 0, 3, "10.00", "0.00"),
                (bulle, 1, None, "0.00", "10.00"),
            ]),
            ("Torneo 23", "2025-07-28", 20, [
                (fili, 2, 2, "40.00", "40.00"),
                (pippi, 0, 3, "10.00", "0.00"),
                (dadde, 0, 1, "100.00", "0.00"),
                (gero, 1, None, "0.00", "10.00"),
                (poltro, 0, None, "0.00", "0.00"),
            ]),
            ("Torneo 24", "2025-09-03", 20, [
                (fili, 4, None, "0.00", "80.00"),
                (pippi, 0, 2, "85.00", "0.00"),
                (dadde, 1, 3, "20.00", "20.00"),
                (gigi, 1, 1, "95.00", "20.00"),
            ]),
            ("Torneo 25", "2025-09-09", 20, [
                (fili, 6, 3, "20.00", "120.00"),
                (pippi, 2, 2, "70.00", "40.00"),
                (dadde, 0, 1, "170.00", "0.00"),
                (cri, 1, None, "0.00", "20.00"),
            ]),
            ("Torneo 26", "2025-09-15", 10, [
                (fili, 0, 2, "35.00", "0.00"),
                (dadde, 3, 1, "85.00", "30.00"),
                (gigi, 3, None, "0.00", "30.00"),
                (dario, 0, None, "0.00", "0.00"),
                (pippi, 1, 3, "10.00", "10.00"),
                (pilo, 0,None, "0.00", "0.00")
            ]),
            ("Torneo 27", "2025-09-25", 20, [
                (fili, 0, None, "0.00", "0.00"),
                (dadde, 0, None, "0.00", "00.00"),
                (gigi, 0, 1, "70.00", "0.00"),
                (pippi, 1, 2, "30.00", "20.00")
            ]),
            ("Torneo 28", "2025-09-25", 20, [
                (fili, 2, 3, "10.00", "40.00"),
                (dadde, 0, 1, "75.00", "0.00"),
                (gigi, 0, None, "0.00", "0.00"),
                (pippi, 0, 2, "35.00", "0.00")
            ]),
            ("Torneo 29", "2025-09-30", 20, [
                (fili, 4, 1, "140.00", "80.00"),
                (dadde, 2, None, "0.00", "40.00"),
                (cri, 0, 2, "60.00", "0.00"),
                (pippi, 1, 3, "20.00", "20.00")
            ]),
            ("Torneo 30", "2025-10-09", 20, [
                (fili, 8, None, "0.00", "160.00"),
                (dadde, 0, None, "0.00", "0.00"),
                (gigi, 0, 1, "155.00", "0.00"),
                (pilo, 0, 3, "20.00", "0.00"),
                (pippi, 0, 2, "85.00", "0.00")
            ]),
            ("Torneo 31", "2025-10-16", 20, [
                (fili, 4, 3, "20.00", "80.00"),
                (dadde, 0, 2, "65.00", "0.00"),
                (gigi, 2, None, "0.00", "40.00"),
                (cri, 1, None, "0.00", "20.00"),
                (pippi, 0, 1, "155.00", "0.00")
            ]),
            ("Torneo 32", "2025-10-22", 30, [
                (fili, 0, 1, "110.00", "0.00"),
                (dadde, 0, 2, "50.00", "0.00"),
                (cri, 1, None, "0.00", "30.00"),
                (pippi, 1, 3, "20.00", "30.00")
            ]),
            ("Torneo 33", "2025-10-30", 30, [
                (fili, 1, None, "0.00", "30.00"),
                (dadde, 0, 1, "150.00", "0.00"),
                (gigi, 0, 2, "60.00", "0.00"),
                (cri, 0, 3, "30.00", "0.00"),
                (pippi, 1, None, "0.00", "30.00"),
                (pilo, 0, None, "0.00", "0.00")
            ]),
                ("Torneo 34", "2025-11-13", 30, [
                (fili, 1, None, "0.00", "30.00"),
                (dadde, 0, 2, "60.00", "0.00"),
                (gigi, 0, 1, "120.00", "0.00"),
                (pippi, 0, 3, "30.00", "0.00"),
                (pilo, 1, None, "0.00", "30.00")
            ]),
        ]

        print(f"🏆 Elaborazione di {len(tornei)} tornei...")

        for nome, data_str, buy_in, partecipanti in tornei:
            # Converte stringa data in oggetto datetime.date
            data_torneo = datetime.strptime(data_str, "%Y-%m-%d").date()

            # Verifica duplicati (utile se esegui lo script più volte senza drop_all)
            existing_trn = db.session.scalar(db.select(Tournament).filter_by(name=nome))
            if existing_trn:
                continue

            torneo = Tournament(
                name=nome,
                tournament_date=data_torneo,
                buy_in=Decimal(buy_in),
                admin=dadde, 
            )
            db.session.add(torneo)
            db.session.flush()  # Ottiene l'ID del torneo prima del commit

            for player, rebuy, position, prize_str, rebuy_total_spent in partecipanti:
                tp = TournamentPlayer(
                    tournament_id=torneo.id,
                    player_id=player.id,
                    rebuy=rebuy,
                    posizione=position,
                    prize=Decimal(prize_str),
                    rebuy_total_spent=rebuy_total_spent
                )
                db.session.add(tp)

            # Calcola il prize pool totale
            total_buy_in = Decimal(buy_in) * len(partecipanti)
            total_rebuy_spent = sum(
                Decimal(p[1]) * Decimal(buy_in) for p in partecipanti
            )
            torneo.prize_pool = total_buy_in + total_rebuy_spent

        db.session.commit()
        print("✅ Database popolato con successo!")

if __name__ == "__main__":
    populate()