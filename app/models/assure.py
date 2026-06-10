import uuid
import enum
from datetime import datetime, date

from sqlalchemy import String, Date, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class PreferencePaiementEnum(str, enum.Enum):
    VIREMENT_BANCAIRE = "VIREMENT_BANCAIRE"
    ESPECES           = "ESPECES"
    MOBILE_MONEY      = "MOBILE_MONEY"


class Assure(Base):
    __tablename__ = "assures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    numero_assure: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    date_naissance: Mapped[date] = mapped_column(Date, nullable=False)
    adresse: Mapped[str] = mapped_column(Text, nullable=True)
    telephone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)

    # Colonne présente dans la base — valeur par défaut pour éviter NotNullViolation
    preference_paiement: Mapped[str] = mapped_column(
        String(50), nullable=False, default="VIREMENT_BANCAIRE",
        server_default="VIREMENT_BANCAIRE"
    )

    # Médecin traitant (généraliste uniquement)
    medecin_traitant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medecins.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relations
    medecin_traitant: Mapped["Medecin"] = relationship(
        "Medecin", foreign_keys=[medecin_traitant_id], back_populates="assures_traites"
    )
    feuilles_maladie: Mapped[list["FeuilleMaladie"]] = relationship(
        "FeuilleMaladie", back_populates="assure", cascade="all, delete-orphan"
    )
    remboursements: Mapped[list["Remboursement"]] = relationship(
        "Remboursement", back_populates="assure"
    )

    def __repr__(self) -> str:
        return f"<Assure {self.numero_assure} — {self.nom} {self.prenom}>"

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relations
    medecin_traitant: Mapped["Medecin"] = relationship(
        "Medecin", foreign_keys=[medecin_traitant_id], back_populates="assures_traites"
    )
    feuilles_maladie: Mapped[list["FeuilleMaladie"]] = relationship(
        "FeuilleMaladie", back_populates="assure", cascade="all, delete-orphan"
    )
    remboursements: Mapped[list["Remboursement"]] = relationship(
        "Remboursement", back_populates="assure"
    )

    def __repr__(self) -> str:
        return f"<Assure {self.numero_assure} — {self.nom} {self.prenom}>"
