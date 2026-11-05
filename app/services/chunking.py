import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.schemas import DocumentChunk


class ChunkingService:
    def chunk_document(
            self,
            document_id: str,
            context: str,
            metadata: dict,
            chunk_size: int = 500,
            chunk_overlap: int = 50) -> list[DocumentChunk]:

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""])
            raw_chunks = splitter.split_text(context)
            chunks = []

            for idx, text in enumerate(raw_chunks):
                chunk = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=idx,
                    content=text,
                    metadata={
                        **metadata,
                        "chunk_index": idx,
                        "document_id": document_id
                    }
                )
                chunks.append(chunk)

            return chunks

chunking_service = ChunkingService()
