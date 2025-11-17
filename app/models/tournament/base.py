# app/models/tournament/base.py

"""
Modello Torneo (Core Entity).

Questo modulo definisce l'entità `Tournament`, che rappresenta l'evento centrale dell'applicazione.
Il modello gestisce i dati strutturali (date, luoghi, buy-in) e funge da aggregatore
per le iscrizioni dei giocatori (`TournamentPlayer`).

Pattern utilizzato:
- Separation of Concerns: Le statistiche complesse sono iniettate via decoratore (@add_stats_properties).
- Data Integrity: Validazione stretta sui tipi decimali per la gestione finanziaria.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Union
from werkzeug.utils import cached_property

from sqlalchemy import Integer, String, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app import db
from app.models.tournament.stats import add_stats_properties
from app.models.tournament.validators import (
    validate_name,
    validate_buy_in,
    validate_prize_pool,
    validate_location,
    validate_tournament_date,
)

if TYPE_CHECKING:
    # Import localizzati per il Type Checking statico (evita import circolari a runtime)
    from app.models.tournament_player.base import TournamentPlayer
    from app.models.player.base import Player


@add_stats_properties
class Tournament(db.Model):
    """
    Rappresenta un singolo Torneo di Poker.

    Attributi:
    - Gestione Finanziaria: `buy_in` e `prize_pool` usano Decimal per precisione monetaria assoluta.
    - Ownership: Ogni torneo è associato a un 'admin' (l'organizzatore/creatore).
    - Stats: Proprietà calcolate (es. ROI medio, total bankroll) sono iniettate dinamicamente.
    """

    __tablename__ = "tournament"

    # --- Colonne Core ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign Key indicizzata per permettere query veloci tipo "Tutti i tornei di Admin X"
    admin_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("player.id"), nullable=False, index=True
    )
    
    # Nome e Data sono i principali criteri di ricerca/ordinamento, quindi indicizzati.
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tournament_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Numeric(10, 2): Fino a 10 cifre totali, di cui 2 decimali. Ideale per valuta.
    # Evita gli errori di arrotondamento virgola mobile tipici dei float.
    buy_in: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Il montepremi può essere nullo se calcolato dinamicamente o non ancora definito.
    prize_pool: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, default=None
    )
    
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # --- Relazioni ORM ---

    # Accesso all'organizzatore.
    # lazy="joined": Quando carico un Torneo, SQLAlchemy fa subito una JOIN per caricare l'Admin.
    # Ottimizzazione: Riduce le query (N+1 problem) poiché l'autore serve quasi sempre.
    admin: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=[admin_id],
        lazy="joined",  
    )

    # Relazione One-to-Many con i partecipanti (TournamentPlayer).
    # NOTA TECNICA SUL LOADING:
    # Manteniamo la strategia di default (lazy='select') invece di 'selectinload'.
    # L'uso di 'selectinload' qui potrebbe causare conflitti di LoaderStrategy (o ricorsione)
    # se incrociato con le relazioni back-populated complesse nel modello figlio.
    # cascade="all, delete-orphan": Se cancello il torneo, elimino tutte le iscrizioni associate.
    tournament_players: Mapped[List["TournamentPlayer"]] = relationship(
        "TournamentPlayer",
        back_populates="tournament",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Rappresentazione stringa per debugging e log."""
        return (
            f"<Tournament(id={self.id}, name='{self.name}', "
            f"date={self.tournament_date})>"
        )

    # --- Proprietà Calcolate (Helpers) ---

    @cached_property
    def num_players(self) -> int:
        """
        Conta i giocatori iscritti.
        
        Usa @cached_property: Il calcolo avviene solo alla prima chiamata per ogni istanza/richiesta.
        Nota: Esegue una len() sulla lista in memoria. Se i tornei avessero 10k+ iscritti,
        sarebbe meglio una query count() dedicata lato DB. Per il poker (10-100 pax), questo è ottimale.
        """
        return len(self.tournament_players)

    # --- Validatori ORM ---
    # Questi metodi intercettano i dati prima del commit al DB.
    # Delegano la logica specifica al file validators.py per mantenere il modello pulito.

    @validates("name")
    def validate_name_field(self, key: str, value: str) -> str:
        return validate_name(value)

    @validates("buy_in")
    def validate_buy_in_field(
        self, key: str, value: Union[Decimal, float, str]
    ) -> Decimal:
        return validate_buy_in(value)

    @validates("prize_pool")
    def validate_prize_pool_field(
        self, key: str, value: Union[Decimal, float, str, None]
    ) -> Decimal | None:
        return validate_prize_pool(value)

    @validates("location")
    def validate_location_field(
        self, key: str, value: Union[str, None]
    ) -> Union[str, None]:
        return validate_location(value)

    @validates("tournament_date")
    def validate_tournament_date_field(
        self, key: str, value: Union[date, datetime]
    ) -> date:
        return validate_tournament_date(value)