# app/models/roles.py
"""
Gestione Ruoli e Permessi (RBAC).

Questo modulo definisce il modello `Role` e la tabella di associazione per la relazione
Molti-a-Molti con i giocatori (`roles_players`).

Architettura:
Il sistema utilizza un approccio standard Role-Based Access Control.
- Un Player può avere N Ruoli.
- Un Ruolo può essere assegnato a N Player.
- La tabella di associazione gestisce i collegamenti fisici nel DB.

Design Choice:
La tabella di associazione è definita come oggetto `Table` (Core) invece che `Model` (ORM)
perché non contiene colonne aggiuntive (payload) oltre alle Foreign Keys.
"""
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import dell'istanza DB condivisa (Singleton Pattern)
from app import db

# Type Hinting condizionale per evitare import circolari a runtime
if TYPE_CHECKING:
    from app.models.player.base import Player

# --- Tabella di Associazione (Many-to-Many: Role <-> Player) ---
# Definizione esplicita tramite SQLAlchemy Core.
# Necessaria per supportare la relazione `secondary` nel modello Role/Player.
roles_players = Table(
    "roles_players",  # Nome fisico della tabella nel DB
    db.metadata,      # Binding ai metadati dell'istanza SQLAlchemy
    Column(
        "player_id",
        Integer,
        # ondelete="CASCADE": CRUCIALE. Se un Player viene eliminato, 
        # rimuove automaticamente la riga di associazione. Evita orfani.
        ForeignKey("player.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id", 
        Integer, 
        # ondelete="CASCADE": Se un Ruolo viene eliminato, toglie il permesso a tutti gli utenti.
        ForeignKey("role.id", ondelete="CASCADE"), 
        primary_key=True
    ),
    # Nota: La coppia (player_id, role_id) è implicitamente unica poiché entrambe sono Primary Key.
)


class Role(db.Model):
    """
    Modello Ruolo Utente.
    
    Rappresenta un livello di privilegio nel sistema (es. 'admin', 'user', 'tournament_manager').
    Usato dai decoratori di protezione delle rotte (es. @login_required, @roles_required).
    """

    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Name: Identificativo univoco del ruolo (es. "admin"). 
    # Indexed=True per velocizzare i check di autorizzazione frequenti.
    name: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True
    )
    
    # Description: Campo leggibile per UI o documentazione interna (opzionale).
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Relazioni ---
    # Relazione Molti-a-Molti bidirezionale con Player.
    # - secondary: Punta alla tabella di associazione definita sopra.
    # - lazy="select": Carica i player associati in una query separata solo quando richiesto.
    #   Per i ruoli va bene 'select' perché raramente carichiamo *tutti* gli utenti di un ruolo (sarebbero troppi).
    players: Mapped[List["Player"]] = relationship(
        "Player",
        secondary=roles_players,
        back_populates="roles",
        lazy="select",
    )

    def __repr__(self) -> str:
        """Rappresentazione stringa per debugging e shell."""
        return f"<Role id={self.id} name='{self.name}'>"


# --- Utility di Bootstrap ---
def create_default_roles():
    """
    Script di Idempotenza per il seeding dei ruoli.
    
    Crea i ruoli base ('user', 'admin') solo se non esistono già.
    Progettato per essere eseguito all'avvio dell'app o via CLI (`flask init-db`).

    Requires: Application Context attivo.
    """
    default_roles = {
        "user": "Standard user with basic permissions.",
        "admin": "Administrator with full permissions.",
    }
    roles_created = []
    roles_existing = []

    for role_name, description in default_roles.items():
        # Verifica esistenza (Query Scalar per efficienza)
        existing_role = db.session.scalar(db.select(Role).filter_by(name=role_name))
        
        if not existing_role:
            new_role = Role(name=role_name, description=description)
            db.session.add(new_role)
            roles_created.append(role_name)
            # Feedback immediato per logs/CLI
            print(f"Creating default role: {role_name}")
        else:
            roles_existing.append(role_name)
            print(f"Default role already exists: {role_name}")

    # Gestione Transazionale: Commit atomico alla fine del processo.
    if roles_created:
        try:
            db.session.commit()
            print(f"Successfully created roles: {', '.join(roles_created)}")
        except Exception as e:
            db.session.rollback() # Revert totale in caso di errore
            print(f"Error creating default roles: {e}")
    else:
        print("All default roles already existed.")