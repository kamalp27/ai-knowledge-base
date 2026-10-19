from dataclasses import dataclass
from typing import List, Optional
from backend.app.rag.parser import ParsedDocument


@dataclass
class TextChunk:
    """Represents an extracted chunk of text with traceable metadata."""
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int]
    chunk_index: int
    text: str


class TextChunker:
    """Configurable text chunker preserving page and provenance metadata."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, parsed_doc: ParsedDocument, document_id: str) -> List[TextChunk]:
        """Split pages of a parsed document into overlapping text chunks."""
        chunks: List[TextChunk] = []
        global_chunk_index = 0

        for page in parsed_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            page_chunks = self._split_text(page_text)
            for chunk_str in page_chunks:
                clean_chunk = chunk_str.strip()
                if not clean_chunk:
                    continue

                chunk_id = f"{document_id}_c{global_chunk_index}"
                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        filename=parsed_doc.filename,
                        page_number=page.page_number,
                        chunk_index=global_chunk_index,
                        text=clean_chunk,
                    )
                )
                global_chunk_index += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """Split text using sliding window with token/character overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.chunk_overlap
        result: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # If not at the end of the text, try finding a natural split point (newline or sentence end)
            if end < text_len:
                # Look backwards within the overlap window for a newline or space
                lookback_window = text[max(start, end - 100):end]
                split_idx = -1
                for sep in ["\n\n", "\n", ". ", " "]:
                    found = lookback_window.rfind(sep)
                    if found != -1:
                        split_idx = max(start, end - 100) + found + len(sep)
                        break
                if split_idx != -1 and split_idx > start:
                    end = split_idx

            chunk = text[start:end].strip()
            if chunk:
                result.append(chunk)

            # Move start forward
            if end >= text_len:
                break
            start += step

        return result
