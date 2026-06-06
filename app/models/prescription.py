import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class TypePrescriptionEnum(str, enum.Enum):
    MEDICAMENT = "MEDICAMENT"
    CONSULTATION_SPECIALISTE = "CONSULTATION_SPECIALISTE"


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type_prescription: Mapped[TypePrescriptionEnum] = mapped_column(
        Enum(TypePrescriptionEnum), nullable=False
    )
    date_prescription: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Clé étrangère vers la consultation
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultations.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    consultation: Mapped["Consultation"] = relationship(
        "Consultation", back_populates="prescriptions"
    )
    prescription_medicament: Mapped["PrescriptionMedicament"] = relationship(
        "PrescriptionMedicament", back_populates="prescription", uselist=False,
        cascade="all, delete-orphan"
    )
    prescription_consultation: Mapped["PrescriptionConsultation"] = relationship(
        "PrescriptionConsultation", back_populates="prescription", uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Prescription {self.id} [{self.type_prescription}]>"


class PrescriptionMedicament(Base):
    __tablename__ = "prescriptions_medicament"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nom_medicament: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    posologie: Mapped[str] = mapped_column(Text, nullable=False)
    duree_traitement_jours: Mapped[int] = mapped_column(Integer, nullable=False)

    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prescriptions.id"), unique=True, nullable=False
    )

    # Relations
    prescription: Mapped["Prescription"] = relationship(
        "Prescription", back_populates="prescription_medicament"
    )


class PrescriptionConsultation(Base):
    __tablename__ = "prescriptions_consultation"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    motif: Mapped[str] = mapped_column(Text, nullable=False)

    # Médecin spécialiste cible (peut être null si non encore identifié)
    specialiste_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medecins.id"), nullable=True
    )

    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prescriptions.id"), unique=True, nullable=False
    )

    # Relations
    prescription: Mapped["Prescription"] = relationship(
        "Prescription", back_populates="prescription_consultation"
    )
    specialiste: Mapped["Medecin"] = relationship("Medecin")
