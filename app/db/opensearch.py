import logging

from opensearchpy import OpenSearch, helpers

from app.config import settings
from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)

INDEX_NAME = "askmydocs_chunks"


def get_opensearch_client() -> OpenSearch:
    client = OpenSearch(
        hosts=[{"host": settings.OPENSEARCH_HOST, "port": settings.OPENSEARCH_PORT}],
        use_ssl=False,
        verify_certs=False,
    )
    return client


def init_opensearch() -> None:
    client = get_opensearch_client()
    if not client.indices.exists(index=INDEX_NAME):
        index_body = {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            },
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "metadata": {"type": "object"}
                }
            }
        }
        client.indices.create(index=INDEX_NAME, body=index_body)


def delete_chunks_opensearch(document_id: str) -> None:
    """Remove chunks already indexed for this document so re-ingesting is idempotent."""
    try:
        client = get_opensearch_client()
        client.delete_by_query(
            index=INDEX_NAME,
            body={"query": {"term": {"document_id": document_id}}},
            conflicts="proceed",
            refresh=True,
        )
    except Exception:
        logger.exception("Failed to delete existing OpenSearch chunks for document %s", document_id)
        raise


def save_chunks_opensearch(chunks: list[DocumentChunk]) -> None:
    if not chunks:
        return

    try:
        client = get_opensearch_client()
        actions = [
            {
                "_index": INDEX_NAME,
                "_id": str(c.id),
                "_source": {
                    "document_id": c.document_id,
                    "chunk_index": c.chunk_index,
                    "content": c.content,
                    "metadata": c.metadata,
                },
            }
            for c in chunks
        ]
        helpers.bulk(client, actions, refresh=True)
    except Exception:
        logger.exception("Failed to save %d chunks to OpenSearch", len(chunks))
        raise
