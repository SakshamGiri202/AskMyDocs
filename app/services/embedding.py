import threading

from app.config import settings


class EmbeddingService:
    def __init__(self):
        # The model is loaded lazily (on first embed call) so app startup and
        # /health stay fast. Loading also needs no re-entrancy: a lock keeps it
        # safe when ingest is run off the event loop in a thread pool.
        self._model = None
        self._lock = threading.Lock()

    def _get_model(self):
        if self._model is None:
            with self._lock:  # double-checked lazy load
                if self._model is None:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        embedding = self._get_model().encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._get_model().encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


embedding_service = EmbeddingService()
