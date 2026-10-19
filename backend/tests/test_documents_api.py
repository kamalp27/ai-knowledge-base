import io
import pymupdf as fitz
import pytest


def test_upload_txt_document(test_env):
    client = test_env["client"]
    content = b"FastAPI is a modern, fast web framework for building APIs with Python."
    file_tuple = ("fastapi_intro.txt", io.BytesIO(content), "text/plain")

    response = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "fastapi_intro.txt"
    assert data["status"] == "indexed"
    assert data["chunk_count"] >= 1
    assert "document_id" in data
    assert "content_hash" in data


def test_upload_markdown_document(test_env):
    client = test_env["client"]
    content = b"# RAG Architecture\n\nRAG combines retrieval with generative LLMs."
    file_tuple = ("rag_guide.md", io.BytesIO(content), "text/markdown")

    response = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "rag_guide.md"
    assert data["status"] == "indexed"


def test_upload_pdf_document(test_env):
    client = test_env["client"]

    # Generate synthetic PDF bytes
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "ChromaDB is an AI-native open-source embedding database.")
    pdf_bytes = doc.tobytes()
    doc.close()

    file_tuple = ("chroma_manual.pdf", io.BytesIO(pdf_bytes), "application/pdf")
    response = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "chroma_manual.pdf"
    assert data["chunk_count"] >= 1


def test_upload_empty_file_rejected(test_env):
    client = test_env["client"]
    file_tuple = ("empty.txt", io.BytesIO(b""), "text/plain")
    response = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_unsupported_format_rejected(test_env):
    client = test_env["client"]
    file_tuple = ("malicious.exe", io.BytesIO(b"binary"), "application/octet-stream")
    response = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_upload_duplicate_detection(test_env):
    client = test_env["client"]
    content = b"Unique content for duplicate testing."
    file_tuple = ("doc1.txt", io.BytesIO(content), "text/plain")

    # First upload succeeds
    res1 = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    assert res1.status_code == 201
    doc_id = res1.json()["document_id"]

    # Second upload with identical bytes triggers 409 Conflict
    file_tuple2 = ("doc1_copy.txt", io.BytesIO(content), "text/plain")
    res2 = client.post("/api/v1/documents/upload", files={"file": file_tuple2})
    assert res2.status_code == 409
    err = res2.json()["detail"]
    assert err["existing_document_id"] == doc_id


def test_list_and_get_documents(test_env):
    client = test_env["client"]
    file_tuple = ("guide.txt", io.BytesIO(b"Document listing content test."), "text/plain")

    # Upload
    upload_res = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    doc_id = upload_res.json()["document_id"]

    # List
    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    found = any(d["document_id"] == doc_id for d in list_data["documents"])
    assert found is True

    # Get details
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    doc_detail = get_res.json()
    assert doc_detail["document_id"] == doc_id
    assert doc_detail["filename"] == "guide.txt"


def test_get_nonexistent_document(test_env):
    client = test_env["client"]
    response = client.get("/api/v1/documents/non-existent-id")
    assert response.status_code == 404


def test_delete_document_and_vector_consistency(test_env):
    client = test_env["client"]
    vector_store = test_env["vector_store"]
    file_tuple = ("to_delete.txt", io.BytesIO(b"Content that will be deleted."), "text/plain")

    upload_res = client.post("/api/v1/documents/upload", files={"file": file_tuple})
    doc_id = upload_res.json()["document_id"]
    assert vector_store.count() >= 1

    # Delete
    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # Verify no longer in metadata
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 404

    # Verify vector chunks were removed
    assert vector_store.count() == 0


def test_delete_nonexistent_document(test_env):
    client = test_env["client"]
    response = client.delete("/api/v1/documents/unknown-uuid")
    assert response.status_code == 404
