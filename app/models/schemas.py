from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentChunk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: str
    chunk_index: int
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[list[float]] = None
    created_at: datetime = Field(default_factory=utcnow)


class IngestionDocumentRequest(BaseModel):
    document_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_size: int = 500
    chunk_overlap: int = 50

    @model_validator(mode="after")
    def validate_chunking(self) -> "IngestionDocumentRequest":
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must not be negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self


class IngestionDocumentResponse(BaseModel):
    document_id: str
    total_chunks: int
    status: str
