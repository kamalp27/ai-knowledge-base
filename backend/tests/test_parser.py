import pymupdf as fitz
import pytest
from backend.app.rag.parser import DocumentParseError, DocumentParser


def test_parse_text_file(tmp_path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Hello world! This is a test document for RAG parsing.", encoding="utf-8")

    parsed = DocumentParser.parse_file(str(txt_file), "sample.txt")
    assert parsed.filename == "sample.txt"
    assert parsed.total_pages == 1
    assert len(parsed.pages) == 1
    assert parsed.pages[0].page_number == 1
    assert "Hello world!" in parsed.pages[0].text


def test_parse_markdown_file(tmp_path):
    md_file = tmp_path / "readme.md"
    md_file.write_text("# Title\n\nThis is a markdown document.\n\n- Feature A\n- Feature B", encoding="utf-8")

    parsed = DocumentParser.parse_file(str(md_file), "readme.md")
    assert parsed.filename == "readme.md"
    assert parsed.total_pages == 1
    assert "Feature A" in parsed.pages[0].text


def test_parse_pdf_file(tmp_path):
    # Create a small valid synthetic PDF using PyMuPDF
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "First page: Retrieval Augmented Generation is powerful.")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "Second page: Vector databases store dense embeddings.")
    doc.save(str(pdf_path))
    doc.close()

    parsed = DocumentParser.parse_file(str(pdf_path), "sample.pdf")
    assert parsed.filename == "sample.pdf"
    assert parsed.total_pages == 2
    assert len(parsed.pages) == 2
    assert parsed.pages[0].page_number == 1
    assert "Retrieval Augmented Generation" in parsed.pages[0].text
    assert parsed.pages[1].page_number == 2
    assert "Vector databases" in parsed.pages[1].text


def test_parse_empty_pages_pdf(tmp_path):
    # PDF with 1 empty page and 1 populated page
    pdf_path = tmp_path / "mixed.pdf"
    doc = fitz.open()
    doc.new_page()  # empty
    p2 = doc.new_page()
    p2.insert_text((50, 72), "Content on page 2")
    doc.save(str(pdf_path))
    doc.close()

    parsed = DocumentParser.parse_file(str(pdf_path), "mixed.pdf")
    assert parsed.total_pages == 2
    # Only the non-empty page should be extracted
    assert len(parsed.pages) == 1
    assert parsed.pages[0].page_number == 2


def test_parse_malformed_pdf(tmp_path):
    bad_pdf = tmp_path / "corrupted.pdf"
    bad_pdf.write_bytes(b"NOT_A_VALID_PDF_HEADER_JUST_GARBAGE_BYTES")

    with pytest.raises(DocumentParseError) as exc_info:
        DocumentParser.parse_file(str(bad_pdf), "corrupted.pdf")
    assert "Failed to open PDF" in str(exc_info.value)


def test_parse_unsupported_extension(tmp_path):
    unsupported = tmp_path / "data.csv"
    unsupported.write_text("a,b,c\n1,2,3", encoding="utf-8")

    with pytest.raises(DocumentParseError) as exc_info:
        DocumentParser.parse_file(str(unsupported), "data.csv")
    assert "Unsupported file format" in str(exc_info.value)
