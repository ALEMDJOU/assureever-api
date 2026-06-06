import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ModePaiementEnum(str, enum.Enum):
    VIREMENT_BANCAIRE = "VIREMENT_BANCAIRE"
    ESPECES = "ESPECES"


class StatutRemboursementEnum(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    PAYE = "PAYE"
    ANNULE = "ANNULE"


class Remboursement(Base):
    __tablename__ = "remboursements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Taux appliqué : 100.0 pour généraliste, 80.0 pour spécialiste
    taux_remboursement: Mapped[float] = mapped_column(Float, nullable=False)
    montant_consultation: Mapped[float] = mapped_column(Float, nullable=False)
    montant_rembourse: Mapped[float] = mapped_column(Float, nullable=False)
    mode_paiement: Mapped[ModePaiementEnum] = mapped_column(Enum(ModePaiementEnum), nullable=False)
    statut: Mapped[StatutRemboursementEnum] = mapped_column(
        Enum(StatutRemboursementEnum),
        default=StatutRemboursementEnum.EN_ATTENTE,
        nullable=False,
    )
    # Référence bancaire pour les virements
    reference_virement: Mapped[str] = mapped_column(String(100), nullable=True)
    # Chemin vers la facture PDF archivée
    facture_path: Mapped[str] = mapped_column(String(500), nullable=True)

    # Clés étrangères
    assure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assures.id"), nullable=False
    )
    feuille_maladie_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("feuilles_maladie.id"), unique=True, nullable=False
    )

    date_remboursement: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    assure: Mapped["Assure"] = relationship("Assure", back_populates="remboursements")
    feuille_maladie: Mapped["FeuilleMaladie"] = relationship(
        "FeuilleMaladie", back_populates="remboursement"
    )

    def __repr__(self) -> str:
        return f"<Remboursement {self.id} — {self.montant_rembourse} FCFA [{self.statut}]>"
