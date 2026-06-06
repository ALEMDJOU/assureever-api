import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class TypeMedecinEnum(str, enum.Enum):
    GENERALISTE = "GENERALISTE"
    SPECIALISTE = "SPECIALISTE"


class Medecin(Base):
    __tablename__ = "medecins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    matricule: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    type_medecin: Mapped[TypeMedecinEnum] = mapped_column(Enum(TypeMedecinEnum), nullable=False)
    specialite: Mapped[str] = mapped_column(String(100), nullable=True)  # Pour les spécialistes
    telephone: Mapped[str] = mapped_column(String(20), nullable=True)

    # Lien vers le compte utilisateur du médecin
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="medecin")
    assures_traites: Mapped[list["Assure"]] = relationship(
        "Assure",
        foreign_keys="Assure.medecin_traitant_id",
        back_populates="medecin_traitant",
    )
    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation", back_populates="medecin"
    )

    def __repr__(self) -> str:
        return f"<Medecin {self.matricule} — {self.nom} [{self.type_medecin}]>"
