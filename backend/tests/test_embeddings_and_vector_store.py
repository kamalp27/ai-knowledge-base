import os
from backend.app.models.documents import DocumentMetadata
from backend.app.rag.chunker import TextChunk
from backend.app.rag.embeddings import DeterministicFakeEmbeddingService
from backend.app.rag.metadata_repository import MetadataRepository
from backend.app.rag.vector_store import ChromaVectorStore, InMemoryVectorStore


def test_fake_embedding_service_properties():
    emb_service = DeterministicFakeEmbeddingService(dimension=32)
    assert emb_service.dimension == 32

    # Determinism: same input produces identical vector
    v1 = emb_service.embed_query("artificial intelligence")
    v2 = emb_service.embed_query("artificial intelligence")
    assert v1 == v2
    assert len(v1) == 32

    # Different inputs produce different vectors
    v3 = emb_service.embed_query("completely different topic")
    assert v1 != v3

    # Batch embedding
    batch = emb_service.embed_texts(["text 1", "text 2"])
    assert len(batch) == 2
    assert len(batch[0]) == 32


def test_in_memory_vector_store_operations():
    store = InMemoryVectorStore()
    emb_service = DeterministicFakeEmbeddingService(dimension=16)

    chunks = [
        TextChunk(
            chunk_id="d1_c0",
            document_id="d1",
            filename="d1.txt",
            page_number=1,
            chunk_index=0,
            text="Vector databases enable fast semantic similarity search.",
        ),
        TextChunk(
            chunk_id="d1_c1",
            document_id="d1",
            filename="d1.txt",
            page_number=1,
            chunk_index=1,
            text="Embeddings map natural language to high-dimensional space.",
        ),
    ]

    embeddings = emb_service.embed_texts([c.text for c in chunks])
    store.add_chunks(chunks, embeddings)
    assert store.count() == 2

    # Query
    q_emb = emb_service.embed_query("semantic search")
    results = store.query_similarity(q_emb, top_k=2)
    assert len(results) == 2
    assert results[0].document_id == "d1"
    assert results[0].score >= 0.0

    # Delete
    deleted_count = store.delete_document("d1")
    assert deleted_count == 2
    assert store.count() == 0


def test_metadata_repository_sqlite(tmp_path):
    db_file = tmp_path / "metadata_test.db"
    repo = MetadataRepository(str(db_file))

    doc = DocumentMetadata(
        document_id="doc-abc",
        filename="report.pdf",
        file_size_bytes=4096,
        content_hash="hash123",
        chunk_count=5,
        created_at="2026-10-20T00:00:00Z",
        status="indexed",
    )

    # Add and retrieve
    repo.add_document(doc, file_path="/fake/path/report.pdf")
    fetched = repo.get_document_by_id("doc-abc")
    assert fetched is not None
    assert fetched.document_id == "doc-abc"
    assert fetched.filename == "report.pdf"
    assert fetched.chunk_count == 5

    # Retrieve by hash (duplicate check)
    by_hash = repo.get_document_by_hash("hash123")
    assert by_hash is not None
    assert by_hash.document_id == "doc-abc"

    # List
    all_docs = repo.list_documents()
    assert len(all_docs) == 1

    # Delete
    deleted = repo.delete_document("doc-abc")
    assert deleted is True
    assert repo.get_document_by_id("doc-abc") is None
    assert len(repo.list_documents()) == 0


def test_chroma_vector_store_real_integration(tmp_path):
    chroma_dir = str(tmp_path / "chroma_real_db")
    store = ChromaVectorStore(persist_directory=chroma_dir, collection_name="test_coll")
    emb_service = DeterministicFakeEmbeddingService(dimension=16)

    chunks = [
        TextChunk(
            chunk_id="chunk_a",
            document_id="doc_a",
            filename="a.txt",
            page_number=1,
            chunk_index=0,
            text="Sentence transformers provide dense semantic vectors.",
        ),
        TextChunk(
            chunk_id="chunk_b",
            document_id="doc_a",
            filename="a.txt",
            page_number=2,
            chunk_index=1,
            text="ChromaDB persists vector embeddings locally on disk.",
        ),
    ]

    embeddings = emb_service.embed_texts([c.text for c in chunks])
    store.add_chunks(chunks, embeddings)
    assert store.count() == 2

    # Query
    q_emb = emb_service.embed_query("dense vectors")
    results = store.query_similarity(q_emb, top_k=2)
    assert len(results) == 2
    assert results[0].document_id == "doc_a"
    assert results[0].score >= 0.0

    # Delete
    del_count = store.delete_document("doc_a")
    assert del_count == 2
    assert store.count() == 0
