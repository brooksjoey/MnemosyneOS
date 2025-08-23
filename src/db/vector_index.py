src/db/vector_index.py
from sqlalchemy import text
from sqlalchemy.engine import Connection

CREATE_HNSW = """
CREATE INDEX IF NOT EXISTS idx_memories_embedding_hnsw
ON memories USING hnsw (embedding vector_cosine_ops)
WITH (m=16, ef_construction=128);
"""

CREATE_FTS = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_attribute
        WHERE attrelid = 'memories'::regclass AND attname = 'tsv') THEN
        ALTER TABLE memories ADD COLUMN tsv tsvector
            GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
    END IF;
END$$;
CREATE INDEX IF NOT EXISTS idx_memories_tsv ON memories USING GIN (tsv);
"""

def ensure_indexes(conn: Connection):
    conn.execute(text(CREATE_HNSW))
    conn.execute(text(CREATE_FTS))

def set_ivfflat_probes(conn: Connection, probes: int = 8):
    conn.execute(text(f"SET ivfflat.probes={probes};"))