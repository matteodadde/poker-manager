# app/models/tournament_player/base.py

"""
Modello di Associazione: TournamentPlayer.

Questo modulo definisce l'Association Object che collega `Tournament` e `Player`.
A differenza di una semplice tabella di associazione (M:N), questa classe
modella l'entità "Partecipazione" o "Iscrizione", contenendo lo stato
specifico di quel giocatore in quel preciso torneo (piazzamento, soldi spesi, premi vinti).

Pattern: SQLAlchemy Association Object.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional, TYPE_CHECKING, Union

from sqlalchemy import Integer, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app import db
from app.models.tournament_player.stats import add_stats_properties
from app.models.tournament_player.validators import (
    validate_rebuy,
    validate_rebuy_total_spent,
    validate_posizione,
    validate_prize,
)

if TYPE_CHECKING:
    # Import per il type checking statico, evita cicli a runtime
    from app.models.tournament.base import Tournament
    from app.models.player.base import Player


@add_stats_properties
class TournamentPlayer(db.Model):
    """
    Rappresenta l'iscrizione di un Giocatore a un Torneo.

    Questa classe funge da ponte tra le tabelle 'tournament' e 'player'.
    Gestisce la persistenza dei risultati sportivi (posizione) e finanziari (rebuy, premi).
    """

    __tablename__ = "tournament_player"

    # --- Composite Primary Key ---
    # La combinazione di tournament_id e player_id è unica.
    # Un giocatore non può iscriversi due volte allo stesso torneo.
    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournament.id"), primary_key=True
    )
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"), primary_key=True)

    # --- Dati di Partecipazione ---
    
    # Posizione finale in classifica (Null se il torneo è in corso o il giocatore non è classificato).
    posizione: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Contatore dei Rebuy effettuati (Default 0).
    rebuy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Somma monetaria spesa per i Rebuy. 
    # È separata dal conteggio 'rebuy' perché il costo potrebbe variare o essere scontato.
    rebuy_total_spent: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    
    # Premio vinto (Cash Out). Null se il giocatore non è andato a premio (ITM).
    prize: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # --- Relazioni ORM ---
    
    # Accesso all'oggetto Torneo genitore.
    # NOTA TECNICA: Usiamo il loading di default ('select') invece di 'joined' o 'subquery'.
    # Questo è intenzionale per rompere potenziali cicli di caricamento (Circular Dependency)
    # quando si serializzano oggetti annidati o si usano i back_populates complessi.
    tournament: Mapped[Tournament] = relationship(
        "Tournament", back_populates="tournament_players"
    )

    # Accesso all'oggetto Player genitore.
    # Anche qui manteniamo il loading lazy/select per pulizia e performance,
    # evitando di caricare l'intero grafo utente se stiamo solo analizzando statistiche del torneo.
    player: Mapped[Player] = relationship("Player", back_populates="tournament_players")

    # Configurazione specifica per database che non supportano autoincrement su chiavi composte (es. SQLite legacy).
    __table_args__ = ({"sqlite_autoincrement": False},)

    # ... (il resto del file rimane invariato) ...

    def update_rebuy_total_spent(self, use_half_price: bool = True) -> None:
        """
        Calcola e aggiorna la spesa totale dei rebuy.
        
        Logica di Business:
        Molti tornei amatoriali applicano una regola dove il Rebuy costa la metà del Buy-in iniziale.
        Questo metodo incapsula questa logica, permettendo di passare `use_half_price=False`
        per tornei "full price".

        Args:
            use_half_price (bool): Se True, calcola il costo rebuy come 50% del buy-in.
                                   Se False, usa il 100% del buy-in.

        Raises:
            ValueError: Se la relazione 'tournament' non è stata caricata (eagerly o lazy)
                        prima di chiamare questo metodo.
        """
        if hasattr(self, "tournament") and self.tournament is not None:
            old_value = self.rebuy_total_spent
            
            # Determinazione del costo unitario del rebuy
            rebuy_cost = (
                (self.tournament.buy_in / 2)
                if use_half_price
                else self.tournament.buy_in
            )
            
            # Calcolo e aggiornamento atomico sull'istanza
            self.rebuy_total_spent = (self.rebuy * rebuy_cost).quantize(Decimal("0.01"))

            logging.debug(
                f"Aggiornamento spesa rebuy player_id={self.player_id}: "
                f"{old_value} -> {self.rebuy_total_spent} (Modalità metà prezzo={use_half_price})"
            )
        else:
            # Fail-safe: Non possiamo calcolare i costi se non sappiamo quanto costa il torneo.
            raise ValueError(
                "Relazione 'tournament' non caricata. "
                "Impossibile calcolare rebuy_total_spent senza conoscere il buy-in."
            )

    def __repr__(self) -> str:
        """Rappresentazione compatta per log di debug e shell."""
        return (
            f"<TournamentPlayer(t_id={self.tournament_id}, p_id={self.player_id}, "
            f"pos={self.posizione}, rebuy={self.rebuy}, prize={self.prize})>"
        )

    # --- Validatori SQLAlchemy (Data Integrity) ---
    # Questi metodi delegano la validazione pura al modulo `validators.py`
    # per mantenere la logica di controllo separata dalla definizione dello schema.

    @validates("rebuy")
    def validate_rebuy_field(self, key: str, value: int) -> int:
        return validate_rebuy(value)

    @validates("rebuy_total_spent")
    def validate_rebuy_total_spent_field(
        self, key: str, value: Union[Decimal, float, str]
    ) -> Decimal:
        # Passiamo 'self' perché la validazione della spesa potrebbe dipendere
        # dal buy-in del torneo associato (validazione contestuale).
        return validate_rebuy_total_spent(self, value)

    @validates("posizione")
    def validate_posizione_field(self, key: str, value: Optional[int]) -> Optional[int]:
        return validate_posizione(value)

    @validates("prize")
    def validate_prize_field(
        self, key: str, value: Union[Decimal, float, str, None]
    ) -> Optional[Decimal]:
        return validate_prize(value)