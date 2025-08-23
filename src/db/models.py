src/db/models.py
import uuid, datetime as dt
from sqlalchemy import Column, DateTime, String, Index, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from .base import Base

class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(String)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    keywords: Mapped[str | None] = mapped_column(String, nullable=True)  # reserved
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    journal_entries = relationship("JournalEntry", back_populates="memory")

    __table_args__ = (
        Index("ix_memories_source_hash", "source_id", "content_hash", unique=True),
    )

class JournalEntry(Base):
    __tablename__ = "journal"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("memories.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB)
    checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    memory = relationship("Memory", back_populates="journal_entries")
    __table_args__ = (Index("ix_journal_created", "created_at"),)

class Belief(Base):
    __tablename__ = "beliefs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject: Mapped[str] = mapped_column(String(256), index=True)
    predicate: Mapped[str] = mapped_column(String(128), index=True)
    object: Mapped[str] = mapped_column(String(512))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    source_id: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    __table_args__ = (Index("ix_belief_spo", "subject", "predicate", "object", unique=False),)