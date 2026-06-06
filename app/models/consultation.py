import uuid
from datetime import datetime, date

from sqlalchemy import String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date_consultation: Mapped[date] = mapped_column(Date, nullable=False)
    motif: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostic: Mapped[str] = mapped_column(Text, nullable=True)
    actes_realises: Mapped[str] = mapped_column(Text, nullable=True)
    montant_consultation: Mapped[float] = mapped_column(nullable=False, default=0.0)

    # Clés étrangères
    assure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assures.id"), nullable=False
    )
    medecin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medecins.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    assure: Mapped["Assure"] = relationship("Assure")
    medecin: Mapped["Medecin"] = relationship("Medecin", back_populates="consultations")
    feuille_maladie: Mapped["FeuilleMaladie"] = relationship(
        "FeuilleMaladie", back_populates="consultation", uselist=False
    )
    prescriptions: Mapped[list["Prescription"]] = relationship(
        "Prescription", back_populates="consultation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Consultation {self.id} — {self.date_consultation}>"
