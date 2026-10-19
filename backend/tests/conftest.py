import os
import pytest
from fastapi.testclient import TestClient
from backend.app.core.config import Settings, get_settings
from backend.app.main import app
from backend.app.rag.dependencies import (
    get_embedding_service,
    get_llm_provider_dep,
    get_metadata_repository,
    get_vector_store,
)
from backend.app.rag.embeddings import DeterministicFakeEmbeddingService
from backend.app.rag.llm import FakeLLMProvider
from backend.app.rag.metadata_repository import MetadataRepository
from backend.app.rag.vector_store import InMemoryVectorStore


@pytest.fixture(scope="session")
def client():
    """Basic test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_env(tmp_path):
    """Provides isolated temporary environment with fast test-doubles."""
    temp_dir = tmp_path / "rag_data"
    temp_docs = temp_dir / "raw_documents"
    temp_db = temp_dir / "metadata.db"
    temp_vector = temp_dir / "vector_store"
    temp_docs.mkdir(parents=True, exist_ok=True)

    metadata_repo = MetadataRepository(str(temp_db))
    embedding_service = DeterministicFakeEmbeddingService(dimension=32)
    vector_store = InMemoryVectorStore()
    llm_provider = FakeLLMProvider()

    test_settings = Settings(
        DATA_DIR=str(temp_dir),
        RAW_DOCUMENTS_DIR=str(temp_docs),
        VECTOR_STORE_DIR=str(temp_vector),
        METADATA_DB_PATH=str(temp_db),
        LLM_PROVIDER="fake",
    )

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_metadata_repository] = lambda: metadata_repo
    app.dependency_overrides[get_embedding_service] = lambda: embedding_service
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_llm_provider_dep] = lambda: llm_provider

    with TestClient(app) as test_client:
        yield {
            "client": test_client,
            "metadata_repo": metadata_repo,
            "embedding_service": embedding_service,
            "vector_store": vector_store,
            "llm_provider": llm_provider,
            "temp_dir": temp_dir,
            "settings": test_settings,
        }

    app.dependency_overrides.clear()
