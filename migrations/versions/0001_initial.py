migrations/versions/0001_initial.py
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None

def upgrade():
    op.create_table(
        "memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("embedding", Vector(1536)),
        sa.Column("keywords", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_memories_source_hash", "memories", ["source_id", "content_hash"], unique=True)
    # FTS column + index
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_attribute
            WHERE attrelid = 'memories'::regclass AND attname = 'tsv') THEN
            ALTER TABLE memories ADD COLUMN tsv tsvector
                GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
        END IF;
    END$$;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_memories_tsv ON memories USING GIN (tsv);")

    op.create_table(
        "journal",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("memories.id"), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_journal_created", "journal", ["created_at"])

    op.create_table(
        "beliefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject", sa.String(256), nullable=False),
        sa.Column("predicate", sa.String(128), nullable=False),
        sa.Column("object", sa.String(512), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.5"),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_belief_spo", "beliefs", ["subject", "predicate", "object"], unique=False)

def downgrade():
    op.drop_table("beliefs")
    op.drop_table("journal")
    op.drop_table("memories")