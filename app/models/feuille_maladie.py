import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class StatutFeuilleEnum(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    COMPLETE = "COMPLETE"
    REMBOURSEE = "REMBOURSEE"


class FeuilleMaladie(Base):
    __tablename__ = "feuilles_maladie"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    statut: Mapped[StatutFeuilleEnum] = mapped_column(
        Enum(StatutFeuilleEnum), default=StatutFeuilleEnum.EN_ATTENTE, nullable=False
    )
    montant_consultation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    observations: Mapped[str] = mapped_column(Text, nullable=True)

    # Clés étrangères
    assure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assures.id"), nullable=False
    )
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id"), unique=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relations
    assure: Mapped["Assure"] = relationship("Assure", back_populates="feuilles_maladie")
    consultation: Mapped["Consultation"] = relationship(
        "Consultation", back_populates="feuille_maladie"
    )
    remboursement: Mapped["Remboursement"] = relationship(
        "Remboursement", back_populates="feuille_maladie", uselist=False
    )

    def __repr__(self) -> str:
        return f"<FeuilleMaladie {self.id} [{self.statut}]>"
