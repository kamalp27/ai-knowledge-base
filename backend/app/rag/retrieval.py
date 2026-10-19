from typing import List
from backend.app.models.query import RetrievedChunk
from backend.app.rag.embeddings import BaseEmbeddingService
from backend.app.rag.vector_store import BaseVectorStore


class RetrievalService:
    """Service orchestrating query embedding and vector similarity retrieval."""

    def __init__(
        self,
        embedding_service: BaseEmbeddingService,
        vector_store: BaseVectorStore,
        similarity_threshold: float = 0.0,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.similarity_threshold = similarity_threshold

    def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
        """Encode query text and retrieve top_k most similar document chunks."""
        clean_query = query.strip()
        if not clean_query:
            return []

        # Vector store count check
        if self.vector_store.count() == 0:
            return []

        query_embedding = self.embedding_service.embed_query(clean_query)
        chunks = self.vector_store.query_similarity(query_embedding, top_k=top_k)

        # Filter by minimum similarity score threshold
        filtered = [c for c in chunks if c.score >= self.similarity_threshold]
        return filtered
