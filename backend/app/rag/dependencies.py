from typing import Optional
from fastapi import Depends
from backend.app.core.config import Settings, get_settings
from backend.app.rag.embeddings import BaseEmbeddingService, SentenceTransformerEmbeddingService
from backend.app.rag.ingestion import DocumentIngestionService
from backend.app.rag.llm import BaseLLMProvider, get_llm_provider
from backend.app.rag.metadata_repository import MetadataRepository
from backend.app.rag.query_service import QueryService
from backend.app.rag.retrieval import RetrievalService
from backend.app.rag.vector_store import BaseVectorStore, ChromaVectorStore

# Module-level singletons for performance and reuse
_metadata_repo: Optional[MetadataRepository] = None
_embedding_service: Optional[BaseEmbeddingService] = None
_vector_store: Optional[BaseVectorStore] = None


def get_metadata_repository(settings: Settings = Depends(get_settings)) -> MetadataRepository:
    """Singleton metadata repository matching active settings."""
    global _metadata_repo
    if _metadata_repo is None or _metadata_repo.db_path != settings.METADATA_DB_PATH:
        _metadata_repo = MetadataRepository(db_path=settings.METADATA_DB_PATH)
    return _metadata_repo


def get_embedding_service(settings: Settings = Depends(get_settings)) -> BaseEmbeddingService:
    """Singleton embedding service matching active model configuration."""
    global _embedding_service
    if _embedding_service is None or getattr(_embedding_service, "model_name", None) != settings.EMBEDDING_MODEL:
        _embedding_service = SentenceTransformerEmbeddingService(model_name=settings.EMBEDDING_MODEL)
    return _embedding_service


def get_vector_store(settings: Settings = Depends(get_settings)) -> BaseVectorStore:
    """Singleton persistent Chroma vector store matching active directory."""
    global _vector_store
    if _vector_store is None or getattr(_vector_store, "persist_directory", None) != settings.VECTOR_STORE_DIR:
        _vector_store = ChromaVectorStore(
            persist_directory=settings.VECTOR_STORE_DIR,
            collection_name=settings.CHROMA_COLLECTION_NAME,
        )
    return _vector_store


def get_ingestion_service(
    settings: Settings = Depends(get_settings),
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
    embedding_service: BaseEmbeddingService = Depends(get_embedding_service),
    vector_store: BaseVectorStore = Depends(get_vector_store),
) -> DocumentIngestionService:
    """Factory for document ingestion pipeline."""
    return DocumentIngestionService(
        raw_documents_dir=settings.RAW_DOCUMENTS_DIR,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        metadata_repo=metadata_repo,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


def get_retrieval_service(
    settings: Settings = Depends(get_settings),
    embedding_service: BaseEmbeddingService = Depends(get_embedding_service),
    vector_store: BaseVectorStore = Depends(get_vector_store),
) -> RetrievalService:
    """Factory for retrieval service."""
    return RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        similarity_threshold=settings.SIMILARITY_THRESHOLD,
    )


def get_llm_provider_dep(settings: Settings = Depends(get_settings)) -> BaseLLMProvider:
    """Resolve configured LLM provider or raise configuration error."""
    return get_llm_provider(settings)


def get_query_service(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_provider: BaseLLMProvider = Depends(get_llm_provider_dep),
) -> QueryService:
    """Factory for question answering query service."""
    return QueryService(
        retrieval_service=retrieval_service,
        llm_provider=llm_provider,
    )
