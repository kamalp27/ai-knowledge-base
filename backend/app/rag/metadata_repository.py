import os
import sqlite3
from typing import List, Optional
from backend.app.models.documents import DocumentMetadata


class MetadataRepository:
    """SQLite-backed persistent store for document metadata and ingestion logs."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure parent directory exists
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);"
            )
            conn.commit()

    def add_document(self, doc: DocumentMetadata, file_path: str) -> None:
        """Insert or replace document metadata."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents 
                (document_id, filename, file_path, file_size_bytes, content_hash, chunk_count, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    doc.document_id,
                    doc.filename,
                    file_path,
                    doc.file_size_bytes,
                    doc.content_hash,
                    doc.chunk_count,
                    doc.created_at,
                    doc.status,
                ),
            )
            conn.commit()

    def get_document_by_id(self, document_id: str) -> Optional[DocumentMetadata]:
        """Fetch document metadata by document ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?;",
                (document_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return DocumentMetadata(
                document_id=row["document_id"],
                filename=row["filename"],
                file_size_bytes=row["file_size_bytes"],
                content_hash=row["content_hash"],
                chunk_count=row["chunk_count"],
                created_at=row["created_at"],
                status=row["status"],
            )

    def get_document_by_hash(self, content_hash: str) -> Optional[DocumentMetadata]:
        """Fetch existing document by content hash to detect duplicates."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE content_hash = ?;",
                (content_hash,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return DocumentMetadata(
                document_id=row["document_id"],
                filename=row["filename"],
                file_size_bytes=row["file_size_bytes"],
                content_hash=row["content_hash"],
                chunk_count=row["chunk_count"],
                created_at=row["created_at"],
                status=row["status"],
            )

    def get_file_path(self, document_id: str) -> Optional[str]:
        """Fetch physical storage path of a document."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT file_path FROM documents WHERE document_id = ?;",
                (document_id,),
            )
            row = cursor.fetchone()
            return row["file_path"] if row else None

    def list_documents(self) -> List[DocumentMetadata]:
        """Return all indexed documents sorted by creation date."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC;"
            )
            rows = cursor.fetchall()
            return [
                DocumentMetadata(
                    document_id=r["document_id"],
                    filename=r["filename"],
                    file_size_bytes=r["file_size_bytes"],
                    content_hash=r["content_hash"],
                    chunk_count=r["chunk_count"],
                    created_at=r["created_at"],
                    status=r["status"],
                )
                for r in rows
            ]

    def delete_document(self, document_id: str) -> bool:
        """Delete document record from SQLite database."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE document_id = ?;",
                (document_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
