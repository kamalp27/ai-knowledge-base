from datetime import datetime, timezone
import hashlib
import os
import re
from typing import Tuple
import uuid
from backend.app.models.documents import DocumentMetadata
from backend.app.rag.chunker import TextChunker
from backend.app.rag.embeddings import BaseEmbeddingService
from backend.app.rag.metadata_repository import MetadataRepository
from backend.app.rag.parser import DocumentParseError, DocumentParser
from backend.app.rag.vector_store import BaseVectorStore


class DuplicateDocumentError(Exception):
    """Raised when a document with identical content has already been ingested."""
    def __init__(self, existing_document: DocumentMetadata):
        self.existing_document = existing_document
        super().__init__(f"Document '{existing_document.filename}' with ID '{existing_document.document_id}' is already indexed.")


class DocumentIngestionService:
    """Coordinates document storage, parsing, chunking, embedding, and indexing."""

    def __init__(
        self,
        raw_documents_dir: str,
        chunk_size: int,
        chunk_overlap: int,
        metadata_repo: MetadataRepository,
        embedding_service: BaseEmbeddingService,
        vector_store: BaseVectorStore,
    ):
        self.raw_documents_dir = raw_documents_dir
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.metadata_repo = metadata_repo
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        os.makedirs(raw_documents_dir, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal or unsafe characters."""
        base = os.path.basename(filename)
        clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
        return clean or "document.txt"

    def ingest_document(
        self,
        file_bytes: bytes,
        original_filename: str,
        allow_duplicate: bool = False,
    ) -> Tuple[DocumentMetadata, bool]:
        """Ingest raw document bytes into storage, vector store, and metadata database.
        
        Returns:
            Tuple[DocumentMetadata, bool]: (metadata, is_duplicate)
        """
        if not file_bytes:
            raise ValueError("Uploaded file content cannot be empty.")

        # 1. Compute SHA-256 hash
        content_hash = hashlib.sha256(file_bytes).hexdigest()

        # 2. Check for duplicate content
        existing = self.metadata_repo.get_document_by_hash(content_hash)
        if existing and not allow_duplicate:
            return existing, True

        # 3. Generate safe unique ID and path
        document_id = str(uuid.uuid4())
        safe_name = self._sanitize_filename(original_filename)
        dest_filename = f"{document_id}_{safe_name}"
        stored_path = os.path.join(self.raw_documents_dir, dest_filename)

        # 4. Save raw file locally
        with open(stored_path, "wb") as f:
            f.write(file_bytes)

        try:
            # 5. Parse document
            parsed_doc = DocumentParser.parse_file(stored_path, original_filename)

            # 6. Chunk text
            chunks = self.chunker.chunk_document(parsed_doc, document_id)
            if not chunks:
                raise DocumentParseError(f"No readable text content found in '{original_filename}'.")

            # 7. Embed chunks
            chunk_texts = [c.text for c in chunks]
            embeddings = self.embedding_service.embed_texts(chunk_texts)

            # 8. Index into Vector Store
            self.vector_store.add_chunks(chunks, embeddings)

            # 9. Save Metadata
            doc_metadata = DocumentMetadata(
                document_id=document_id,
                filename=original_filename,
                file_size_bytes=len(file_bytes),
                content_hash=content_hash,
                chunk_count=len(chunks),
                created_at=datetime.now(timezone.utc).isoformat(),
                status="indexed",
            )
            self.metadata_repo.add_document(doc_metadata, stored_path)

            return doc_metadata, False

        except Exception as e:
            # Cleanup stored file on failure to maintain consistency
            if os.path.exists(stored_path):
                try:
                    os.remove(stored_path)
                except OSError:
                    pass
            # Also clean up any vector store entries if partially added
            try:
                self.vector_store.delete_document(document_id)
            except Exception:
                pass
            raise e

    def delete_document(self, document_id: str) -> bool:
        """Atomically delete document file, vector embeddings, and metadata."""
        # 1. Look up file path
        file_path = self.metadata_repo.get_file_path(document_id)

        # 2. Delete vectors from vector store
        self.vector_store.delete_document(document_id)

        # 3. Delete metadata record
        deleted = self.metadata_repo.delete_document(document_id)

        # 4. Remove physical file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        return deleted
