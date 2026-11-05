import logging

from app.models.schemas import IngestionDocumentRequest, IngestionDocumentResponse
from app.services.chunking import chunking_service
from app.services.embedding import embedding_service
from app.db.postgres import save_chunks_pgvector, delete_chunks_pgvector
from app.db.opensearch import save_chunks_opensearch, delete_chunks_opensearch

logger = logging.getLogger(__name__)


class IngestionService:
    def process_and_store(self, request: IngestionDocumentRequest) -> IngestionDocumentResponse:
        # 1 chunk document
        chunks = chunking_service.chunk_document(
            document_id=request.document_id,
            context=request.content,
            metadata=request.metadata,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )

        if not chunks:
            # empty document -> nothing to embed or store
            return IngestionDocumentResponse(
                document_id=request.document_id,
                total_chunks=0,
                status="SUCCESS",
            )

        # make re-ingesting the same document_id idempotent: drop old chunks first
        delete_chunks_pgvector(request.document_id)
        delete_chunks_opensearch(request.document_id)

        # 2 compute embeddings in batch
        texts = [c.content for c in chunks]
        embeddings = embedding_service.embed_batch(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb

        # 3 dual storage write (postgres vector + opensearch bm25)
        save_chunks_pgvector(chunks)
        save_chunks_opensearch(chunks)

        logger.info("Ingested document %s (%d chunks)", request.document_id, len(chunks))

        return IngestionDocumentResponse(
            document_id=request.document_id,
            total_chunks=len(chunks),
            status="SUCCESS",
        )


ingestion_service = IngestionService()
