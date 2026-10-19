import pytest
from backend.app.rag.chunker import TextChunker
from backend.app.rag.parser import ParsedDocument, ParsedPage


def test_chunker_small_text_single_chunk():
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    doc = ParsedDocument(
        filename="test.txt",
        pages=[ParsedPage(page_number=1, text="Short content fitting in one chunk.")],
        total_pages=1,
    )

    chunks = chunker.chunk_document(doc, document_id="doc-123")
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "doc-123_c0"
    assert chunks[0].document_id == "doc-123"
    assert chunks[0].filename == "test.txt"
    assert chunks[0].page_number == 1
    assert chunks[0].text == "Short content fitting in one chunk."


def test_chunker_multi_page_and_overlap():
    chunker = TextChunker(chunk_size=100, chunk_overlap=30)
    long_text_p1 = "Paragraph 1 of page 1. " * 8  # ~184 chars
    text_p2 = "Page 2 content is distinct and specific."

    doc = ParsedDocument(
        filename="multipage.txt",
        pages=[
            ParsedPage(page_number=1, text=long_text_p1),
            ParsedPage(page_number=2, text=text_p2),
        ],
        total_pages=2,
    )

    chunks = chunker.chunk_document(doc, document_id="doc-multi")
    assert len(chunks) >= 3
    # Verify chunk indices increment sequentially
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        assert c.chunk_id == f"doc-multi_c{idx}"

    # Verify page numbers are preserved
    p1_chunks = [c for c in chunks if c.page_number == 1]
    p2_chunks = [c for c in chunks if c.page_number == 2]
    assert len(p1_chunks) >= 2
    assert len(p2_chunks) >= 1
    assert "Page 2 content" in p2_chunks[0].text


def test_chunker_invalid_parameters():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=0, chunk_overlap=0)

    with pytest.raises(ValueError):
        TextChunker(chunk_size=100, chunk_overlap=-1)

    with pytest.raises(ValueError):
        # Overlap cannot be greater than or equal to chunk size
        TextChunker(chunk_size=100, chunk_overlap=100)
