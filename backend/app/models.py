from datetime import datetime, timezone

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP
import enum

from .database import Base


class LabelSource(str, enum.Enum):
    manual = "manual"
    ai     = "ai"


class Contract(Base):
    __tablename__ = "contracts"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True)
    filename:    Mapped[str]      = mapped_column(String(255), nullable=False)
    content:     Mapped[str]      = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sentences: Mapped[list["Sentence"]] = relationship(
        "Sentence",
        back_populates="contract",
        cascade="all, delete-orphan",
        order_by="Sentence.position",
    )


class Sentence(Base):
    __tablename__ = "sentences"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text:        Mapped[str] = mapped_column(Text, nullable=False)
    position:    Mapped[int] = mapped_column(Integer, nullable=False)

    contract: Mapped["Contract"]           = relationship("Contract", back_populates="sentences")
    label:    Mapped["ClauseLabel | None"] = relationship(
        "ClauseLabel",
        back_populates="sentence",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ClauseType(Base):
    __tablename__ = "clause_types"

    id:    Mapped[int] = mapped_column(Integer, primary_key=True)
    name:  Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # "#RRGGBB"

    labels: Mapped[list["ClauseLabel"]] = relationship("ClauseLabel", back_populates="clause_type")


class ClauseLabel(Base):
    __tablename__ = "clause_labels"

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True)
    sentence_id:    Mapped[int]      = mapped_column(
        Integer,
        ForeignKey("sentences.id", ondelete="CASCADE"),
        nullable=False,
    )
    clause_type_id: Mapped[int]      = mapped_column(
        Integer,
        ForeignKey("clause_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source:         Mapped[str]      = mapped_column(
        Enum(LabelSource, name="label_source"),
        default=LabelSource.manual,
        nullable=False,
    )
    labeled_at:     Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sentence:    Mapped["Sentence"]   = relationship("Sentence",   back_populates="label")
    clause_type: Mapped["ClauseType"] = relationship("ClauseType", back_populates="labels")

    __table_args__ = (
        UniqueConstraint("sentence_id", name="uq_clause_labels_sentence_id"),
    )