from abc import ABC, abstractmethod
import hashlib
import math
from typing import List


class BaseEmbeddingService(ABC):
    """Abstract interface for text embedding generation."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a batch of text chunks."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Compute embedding for a single search query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding vector dimension."""
        pass


class SentenceTransformerEmbeddingService(BaseEmbeddingService):
    """Embedding service using Sentence Transformers with lazy model initialization."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384  # standard for all-MiniLM-L6-v2, updated upon model load

    def _get_model(self):
        """Lazy load SentenceTransformer model on first usage."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                if hasattr(self._model, "get_embedding_dimension"):
                    self._dimension = self._model.get_embedding_dimension()
                else:
                    self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers is not installed. Please install dependencies from requirements.txt"
                )
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, query: str) -> List[float]:
        model = self._get_model()
        vec = model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        return vec.tolist()

    @property
    def dimension(self) -> int:
        if self._model is not None:
            return self._dimension
        return 384


class DeterministicFakeEmbeddingService(BaseEmbeddingService):
    """Fast, deterministic embedding service for unit and integration testing.
    
    Generates normalized pseudo-embeddings derived from text hashes so that tests
    do not require network downloads, GPUs, or heavy PyTorch models.
    """

    def __init__(self, dimension: int = 64):
        self._dimension = dimension

    def _hash_to_vector(self, text: str) -> List[float]:
        # Generate deterministic vector using SHA-256 tokens
        vec = []
        for i in range(self._dimension):
            h = hashlib.sha256(f"{text}_{i}".encode("utf-8")).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) - 0.5
            vec.append(val)

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._hash_to_vector(query)

    @property
    def dimension(self) -> int:
        return self._dimension
