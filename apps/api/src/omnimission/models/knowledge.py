"""ORM models for Knowledge Base documents, chunks, and Knowledge Graph."""

import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnimission.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeDoc(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authored structured knowledge document (recipe, trip kit, dietary rule, household guide)."""

    __tablename__ = "knowledge_docs"

    doc_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
    )
    diet_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
    )
    servings_base: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    ingredients: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    summary: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk",
        back_populates="doc",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.chunk_index",
    )


class KnowledgeChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Structure-aware section chunk with dense vector embedding and sparse tsvector."""

    __tablename__ = "knowledge_chunks"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_docs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    section_title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )
    tsv: Mapped[Any | None] = mapped_column(
        TSVECTOR,
        nullable=True,
    )

    doc: Mapped[KnowledgeDoc] = relationship(
        "KnowledgeDoc",
        back_populates="chunks",
    )


class KGNode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Knowledge Graph Entity Node (recipe, ingredient, dietary_tag, occasion, department)."""

    __tablename__ = "kg_nodes"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    properties: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    __table_args__ = (
        UniqueConstraint("name", "entity_type", name="uq_kg_node_name_type"),
    )


class KGEdge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Knowledge Graph Directed Edge (requires, substitutes_for, satisfies_diet, etc.)."""

    __tablename__ = "kg_edges"

    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kg_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kg_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    properties: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    __table_args__ = (
        UniqueConstraint(
            "source_node_id", "target_node_id", "relation_type", name="uq_kg_edge_source_target_rel"
        ),
    )
