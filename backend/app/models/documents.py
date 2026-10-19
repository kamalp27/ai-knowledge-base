from typing import List
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Schema representing indexed document metadata."""

    document_id: str = Field(..., description="Unique UUID assigned to the document")
    filename: str = Field(..., description="Original user-provided filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    content_hash: str = Field(..., description="SHA-256 hash of document raw content")
    chunk_count: int = Field(..., description="Number of text chunks created and indexed")
    created_at: str = Field(..., description="UTC ISO timestamp of ingestion")
    status: str = Field(default="indexed", description="Ingestion status (indexed, failed)")


class DocumentUploadResponse(BaseModel):
    """Schema returned after a successful document upload and indexing."""

    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Status (e.g., indexed, already_indexed)")
    chunk_count: int = Field(..., description="Total chunks extracted and stored")
    file_size_bytes: int = Field(..., description="File size in bytes")
    content_hash: str = Field(..., description="Content SHA-256 hash")
    message: str = Field(..., description="Human-readable status summary")


class DocumentListResponse(BaseModel):
    """Schema returning a list of all indexed documents."""

    total: int = Field(..., description="Total number of indexed documents")
    documents: List[DocumentMetadata] = Field(default_factory=list, description="List of document metadata items")


class DocumentDeleteResponse(BaseModel):
    """Schema returned after document deletion."""

    document_id: str = Field(..., description="Identifier of the deleted document")
    deleted: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")
