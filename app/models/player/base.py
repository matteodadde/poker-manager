# app/models/player/base.py
"""
Definizione del Modello Player (Utente).

Questo modulo definisce l'entità principale del sistema.
Architetturalmente, questo modello unifica due concetti:
1. **Identity Management (User)**: Autenticazione, ruoli, email, password (tramite UserMixin).
2. **Domain Entity (Player)**: Statistiche, partecipazione ai tornei, nickname.

Questa scelta semplifica le relazioni nel database, evitando una tabella 1:1 tra User e Player,
ma richiede che il modello gestisca responsabilità miste (Auth + Business Logic).
"""
import secrets
import datetime
from typing import TYPE_CHECKING, List, Optional
from pathlib import Path  # Necessario per controllare l'esistenza fisica dei file avatar

# SQLAlchemy e ORM tools
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

# Flask & Estensioni
from flask_login import UserMixin  # Fornisce i metodi standard (is_authenticated, ecc.)
from flask import current_app, url_for, has_request_context # Necessari per risolvere i percorsi degli asset statici

# Import interni
from app import db, bcrypt
from app.models.player.validators import (
    validate_name,
    validate_nickname_rules,
    validate_country,
    validate_email_format,
    validate_password_strength,
)
from app.models.player.stats import add_stats_properties
from app.models.roles import Role, roles_players

# Type checking statico per evitare import circolari a runtime
if TYPE_CHECKING:
    from app.models.tournament_player.base import TournamentPlayer


@add_stats_properties
class Player(db.Model, UserMixin):
    """
    Rappresenta un Giocatore registrato nel sistema.
    
    Eredita da:
    - `db.Model`: Per la persistenza su database SQLAlchemy.
    - `UserMixin`: Per l'integrazione immediata con Flask-Login (sessioni).
    
    Decoratori:
    - `@add_stats_properties`: Inietta dinamicamente proprietà calcolate (es. ROI, ITM%)
      mantenendo questo file pulito dalla logica matematica complessa.
    """

    __tablename__ = "player"

    # --- Identificativi e Dati Anagrafici ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Nickname: Chiave di ricerca frequente nei tornei, quindi indicizzata.
    nickname: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    
    # Email: Chiave primaria per il login, deve essere unica e indicizzata.
    email: Mapped[str] = mapped_column(
        String(120), nullable=False, unique=True, index=True
    )
    
    # Password Hash: Nullabile perché un admin potrebbe creare un player
    # che non ha ancora attivato l'account (invito pending).
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    
    # Soft Delete / Ban logic: Invece di cancellare fisicamente, disattiviamo l'utente.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relazioni (ORM) ---
    
    # Relazione 1:N con le partecipazioni ai tornei.
    # cascade="all, delete-orphan": Se cancello il Player, cancello le sue iscrizioni.
    tournament_players: Mapped[List["TournamentPlayer"]] = relationship(
        "TournamentPlayer",
        back_populates="player",
        cascade="all, delete-orphan",
    )

    # Relazione M:N con i Ruoli (RBAC - Role Based Access Control).
    # lazy="select": Carica i ruoli solo quando vengono acceduti (performance optimization).
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=roles_players,
        back_populates="players",
        lazy="select",
    )

    # --- Helper Methods per i Ruoli ---
    
    def has_role(self, role_name: str) -> bool:
        """
        Verifica i permessi dell'utente (Case-insensitive).
        Usa l'iterazione in memoria sui ruoli caricati.
        """
        return any(role.name.lower() == role_name.lower() for role in self.roles)

    @property
    def is_admin(self) -> bool:
        """Shortcut leggibile per verificare i privilegi amministrativi."""
        return self.has_role("admin")

    # --- Gestione Sicurezza Password (Encapsulation) ---
    # Utilizziamo le property per impedire l'accesso diretto alla password in chiaro
    # e garantire che l'hashing avvenga sempre al momento dell'assegnazione.

    @property
    def password(self):
        """
        Impedisce la lettura della password.
        Tentare di leggere `player.password` solleverà un errore intenzionale.
        """
        raise AttributeError("Password is not a readable attribute")

    @password.setter
    def password(self, password: str):
        """
        Setter: Intercetta l'assegnazione della password.
        1. Valida la complessità (Policy).
        2. Genera l'hash sicuro (Bcrypt + Salt).
        3. Salva solo l'hash nel DB.
        """
        validate_password_strength(password)
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """
        Verifica una password in chiaro contro l'hash salvato.
        Gestisce il caso limite di utenti senza password (es. account creati da admin).
        """
        if not self.password_hash:
            return False  # Fail-safe per account non attivati
        return bcrypt.check_password_hash(self.password_hash, password)

    # --- Validatori ORM (Data Integrity Layer) ---
    # Questi metodi intercettano i dati PRIMA che vengano committati nel DB.
    # Garantiscono che il dato salvato sia sempre pulito e conforme, indipendentemente
    # da quale form o API abbia originato la richiesta.

    @validates("first_name")
    def validate_first_name_field(self, key: str, value: str) -> str:
        return validate_name(value, "First Name")

    @validates("last_name")
    def validate_last_name_field(self, key: str, value: str) -> str:
        return validate_name(value, "Last Name")

    @validates("nickname")
    def validate_nickname_field(self, key: str, value: str) -> str:
        cleaned = validate_nickname_rules(value)
        return cleaned

    @validates("email")
    def validate_email_field(self, key: str, value: str) -> str:
        cleaned = validate_email_format(value.lower().strip())  # Normalizzazione forzata
        return cleaned

    @validates("country")
    def validate_country_field(self, key: str, value: Optional[str]) -> Optional[str]:
        return validate_country(value)  # ISO Code validation

    # --- Gestione Avatar (Asset Resolution) ---
    # La logica seguente risolve dinamicamente l'URL dell'immagine.
    # Controlla fisicamente il disco per evitare errori 404 nel client.

    @property
    def avatar_url(self) -> str:
        """
        Genera l’URL per la THUMBNAIL.
        Robusto: funziona anche fuori da una request (test performance).
        """

        # --- 1. Gestione oggetti non salvati ---
        rel_default = "images/default-avatar.png"
        if not self.id:
            # Se NON siamo in una request → no url_for
            if has_request_context():
                return url_for("static", filename=rel_default)
            return f"/static/{rel_default}"

        # --- 2. Path relativi e assoluti ---
        rel_specific = f"images/players/{self.id}.png"
        abs_specific = Path(current_app.static_folder) / rel_specific

        # --- 3. Se esiste file specifico, usa quello ---
        if abs_specific.is_file():
            final_rel = rel_specific
        else:
            final_rel = rel_default

        # --- 4. Se posso usare url_for → lo uso ---
        if has_request_context():
            return url_for("static", filename=final_rel)

        # --- 5. Altrimenti restituisco path statico "finto" ---
        # (serve per performance tests e script)
        return f"/static/{final_rel}"


    @property
    def avatar_url_full(self) -> str:
        """
        Genera l'URL per la versione FULL-SIZE (es. pagina profilo, modale).
        Stessa logica di `avatar_url` ma cerca il suffisso `_full.png`.
        """
        if not self.id:
            return url_for("static", filename="images/default-avatar.png")

        # NOTA: Cerca il file con suffisso '_full'
        specific_avatar_rel_path = f"images/players/{self.id}_full.png"
        default_avatar_rel_path = "images/default-avatar.png"

        static_folder_path = Path(current_app.static_folder)
        specific_avatar_abs_path = static_folder_path / specific_avatar_rel_path

        if specific_avatar_abs_path.is_file():
            return url_for("static", filename=specific_avatar_rel_path)
        else:
            # Fallback graceful: se manca l'alta definizione, mostra il default
            return url_for("static", filename=default_avatar_rel_path)

    # --- String Representation (Debugging) ---
    def __repr__(self) -> str:
        """Rappresentazione per shell/log. Include stato attivazione e ruoli."""
        roles_str = ",".join(r.name for r in self.roles) or "None"
        status = "Active" if self.is_active else "Inactive"
        activated = "Yes" if self.password_hash else "No (Pending Activation)"
        return (
            f"<Player id={self.id} nickname='{self.nickname}' email='{self.email}' "
            f"roles=[{roles_str}] status={status} activated={activated}>"
        )