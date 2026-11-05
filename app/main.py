import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.models.schemas import IngestionDocumentRequest, IngestionDocumentResponse
from app.services.ingestion import ingestion_service
from app.db.postgres import init_postgres
from app.db.opensearch import init_opensearch

logger = logging.getLogger("askmydocs")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialise table schemas and search indices on startup
    init_postgres()
    init_opensearch()
    yield


app = FastAPI(title="AskMyDocs RAG Engine Core", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/v1/ingest", response_model=IngestionDocumentResponse)
async def ingest_document(request: IngestionDocumentRequest):
    try:
        # embedding + DB writes are blocking/sync -> keep the event loop free
        return await run_in_threadpool(ingestion_service.process_and_store, request)
    except HTTPException:
        raise
    except Exception:
        # log the real error server-side; never leak internals to the client
        logger.exception("Ingestion failed for document %s", request.document_id)
        raise HTTPException(status_code=500, detail="Internal error while ingesting document")
