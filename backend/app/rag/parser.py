from dataclasses import dataclass
import os
from typing import List, Optional
import pymupdf as fitz


class DocumentParseError(Exception):
    """Exception raised when document parsing fails."""
    pass


@dataclass
class ParsedPage:
    """Represents text extracted from a document page or segment."""
    page_number: Optional[int]
    text: str


@dataclass
class ParsedDocument:
    """Represents a fully parsed document containing pages/segments."""
    filename: str
    pages: List[ParsedPage]
    total_pages: int


class DocumentParser:
    """Parser supporting PDF, TXT, and Markdown documents."""

    @classmethod
    def parse_file(cls, file_path: str, filename: str) -> ParsedDocument:
        """Parse a document file by extension and extract its text page by page.
        
        Raises:
            DocumentParseError: If file is unsupported, malformed, or cannot be read.
        """
        if not os.path.exists(file_path):
            raise DocumentParseError(f"File not found: {file_path}")

        ext = os.path.splitext(filename.lower())[1]

        if ext == ".pdf":
            return cls._parse_pdf(file_path, filename)
        elif ext in [".txt", ".md"]:
            return cls._parse_text(file_path, filename)
        else:
            raise DocumentParseError(f"Unsupported file format '{ext}'. Allowed: .pdf, .txt, .md")

    @staticmethod
    def _parse_pdf(file_path: str, filename: str) -> ParsedDocument:
        """Extract text from PDF page by page using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise DocumentParseError(f"Failed to open PDF '{filename}': {str(e)}")

        try:
            if doc.is_encrypted:
                raise DocumentParseError(f"Encrypted or password-protected PDF files are not supported: '{filename}'")

            pages: List[ParsedPage] = []
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text("text").strip()
                # Skip empty pages
                if text:
                    pages.append(ParsedPage(page_number=page_index + 1, text=text))

            total_pages = len(doc)
            return ParsedDocument(filename=filename, pages=pages, total_pages=total_pages)
        except DocumentParseError:
            raise
        except Exception as e:
            raise DocumentParseError(f"Error extracting text from PDF '{filename}': {str(e)}")
        finally:
            doc.close()

    @staticmethod
    def _parse_text(file_path: str, filename: str) -> ParsedDocument:
        """Extract text from TXT or Markdown files."""
        content = ""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        read_success = False
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                read_success = True
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if not read_success:
            raise DocumentParseError(f"Could not decode text file '{filename}' with supported encodings.")

        text = content.strip()
        pages: List[ParsedPage] = []
        if text:
            # Plain text and markdown treated as a single page or segmented by form feeds if any
            pages.append(ParsedPage(page_number=1, text=text))

        return ParsedDocument(filename=filename, pages=pages, total_pages=1 if pages else 0)
