import logging
from contextlib import contextmanager

import psycopg2
import psycopg2.pool
from psycopg2.extras import execute_values

from app.config import settings
from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)

_pool = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.DATABASE_URL,
        )
    return _pool


@contextmanager
def get_db_connection():
    """Yield a pooled connection and always return it to the pool."""
    conn = _get_pool().getconn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        _get_pool().putconn(conn)


def init_postgres() -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                create table if not exists document_chunks(
                id uuid primary key,
                document_id varchar(255) not null,
                chunk_index int not null,
                content text not null,
                metadata jsonb not null,
                embedding vector({settings.EMBEDDING_DIM}),
                created_at timestamp with time zone default now()
                );
                """)
            cur.execute("""
                    create index if not exists document_chunks_embedding_hnsw_idx
                    on document_chunks using hnsw (embedding vector_cosine_ops);
                    """)
            conn.commit()


def save_chunks_pgvector(chunks: list[DocumentChunk]) -> None:
    if not chunks:
        return

    query = """ insert into document_chunks (id, document_id, chunk_index, content, metadata, embedding, created_at) values %s;"""

    records = [
        (
            str(c.id),
            c.document_id,
            c.chunk_index,
            c.content,
            psycopg2.extras.Json(c.metadata),
            str(c.embedding),
            c.created_at
        )
        for c in chunks
    ]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, records)
            conn.commit()
    except Exception:
        logger.exception("Failed to save %d chunks to pgvector", len(chunks))
        raise


def delete_chunks_pgvector(document_id: str) -> None:
    """Remove chunks already stored for this document so re-ingesting is idempotent."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "delete from document_chunks where document_id = %s;",
                    (document_id,),
                )
            conn.commit()
    except Exception:
        logger.exception("Failed to delete existing chunks for document %s", document_id)
        raise
