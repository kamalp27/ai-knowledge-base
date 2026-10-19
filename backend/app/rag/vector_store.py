from abc import ABC, abstractmethod
import math
import os
from typing import List, Optional
from backend.app.models.query import RetrievedChunk
from backend.app.rag.chunker import TextChunk


class BaseVectorStore(ABC):
    """Abstract interface for vector database storage and retrieval."""

    @abstractmethod
    def add_chunks(self, chunks: List[TextChunk], embeddings: List[List[float]]) -> None:
        """Store chunk texts, metadata, and embeddings."""
        pass

    @abstractmethod
    def query_similarity(self, query_embedding: List[float], top_k: int) -> List[RetrievedChunk]:
        """Query most similar chunks by vector similarity."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a document ID."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total chunks indexed."""
        pass


class ChromaVectorStore(BaseVectorStore):
    """Persistent ChromaDB vector store implementation."""

    def __init__(self, persist_directory: str, collection_name: str = "knowledge_base"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        os.makedirs(persist_directory, exist_ok=True)
        self._client = None
        self._collection = None

    def _get_collection(self):
        """Lazy initialization of ChromaDB client and collection."""
        if self._collection is None:
            try:
                import chromadb
                self._client = chromadb.PersistentClient(path=self.persist_directory)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except ImportError:
                raise RuntimeError(
                    "chromadb is not installed. Please install dependencies from requirements.txt"
                )
        return self._collection

    def add_chunks(self, chunks: List[TextChunk], embeddings: List[List[float]]) -> None:
        if not chunks:
            return

        collection = self._get_collection()
        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "filename": c.filename,
                "page_number": c.page_number if c.page_number is not None else -1,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query_similarity(self, query_embedding: List[float], top_k: int) -> List[RetrievedChunk]:
        collection = self._get_collection()
        if collection.count() == 0:
            return []

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        retrieved: List[RetrievedChunk] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return retrieved

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else []
        metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for i, chunk_id in enumerate(ids):
            meta = metas[i] if i < len(metas) else {}
            doc_text = docs[i] if i < len(docs) else ""
            dist = distances[i] if i < len(distances) else 1.0
            
            # Cosine distance in chromadb ranges [0, 2]; convert to similarity score in [0, 1]
            score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

            page_num = meta.get("page_number", -1)
            page_val = page_num if page_num != -1 else None

            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=meta.get("document_id", ""),
                    filename=meta.get("filename", "unknown"),
                    page_number=page_val,
                    text=doc_text,
                    score=round(score, 4),
                )
            )

        return retrieved

    def delete_document(self, document_id: str) -> int:
        collection = self._get_collection()
        # Query matching IDs first to return deleted count
        try:
            existing = collection.get(where={"document_id": document_id})
            count = len(existing["ids"]) if existing and "ids" in existing else 0
            if count > 0:
                collection.delete(where={"document_id": document_id})
            return count
        except Exception:
            return 0

    def count(self) -> int:
        collection = self._get_collection()
        return collection.count()


class InMemoryVectorStore(BaseVectorStore):
    """In-memory vector store for lightning-fast testing and fallback."""

    def __init__(self):
        self._chunks: dict[str, TextChunk] = {}
        self._embeddings: dict[str, List[float]] = {}

    def add_chunks(self, chunks: List[TextChunk], embeddings: List[List[float]]) -> None:
        for chunk, emb in zip(chunks, embeddings):
            self._chunks[chunk.chunk_id] = chunk
            self._embeddings[chunk.chunk_id] = emb

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def query_similarity(self, query_embedding: List[float], top_k: int) -> List[RetrievedChunk]:
        scored: List[tuple[float, TextChunk]] = []
        for chunk_id, emb in self._embeddings.items():
            sim = self._cosine_similarity(query_embedding, emb)
            scored.append((sim, self._chunks[chunk_id]))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        return [
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                filename=chunk.filename,
                page_number=chunk.page_number,
                text=chunk.text,
                score=round(max(0.0, min(1.0, (sim + 1.0) / 2.0)), 4),
            )
            for sim, chunk in top
        ]

    def delete_document(self, document_id: str) -> int:
        to_del = [cid for cid, chunk in self._chunks.items() if chunk.document_id == document_id]
        for cid in to_del:
            del self._chunks[cid]
            del self._embeddings[cid]
        return len(to_del)

    def count(self) -> int:
        return len(self._chunks)
