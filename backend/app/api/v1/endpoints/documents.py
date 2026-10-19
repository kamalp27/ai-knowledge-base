import os
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from backend.app.core.config import Settings, get_settings
from backend.app.models.documents import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from backend.app.rag.dependencies import (
    get_ingestion_service,
    get_metadata_repository,
)
from backend.app.rag.ingestion import DocumentIngestionService
from backend.app.rag.metadata_repository import MetadataRepository
from backend.app.rag.parser import DocumentParseError

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Index Document",
    description="Accepts PDF, TXT, or Markdown documents, extracts text page by page, chunks, embeds, and indexes into the knowledge base.",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to ingest (.pdf, .txt, .md)"),
    settings: Settings = Depends(get_settings),
    ingestion_service: DocumentIngestionService = Depends(get_ingestion_service),
) -> DocumentUploadResponse:
    filename = file.filename or "uploaded_document"
    ext = os.path.splitext(filename.lower())[1]

    # 1. Validate file extension
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # 2. Read stream with upload size limit enforcement
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = bytearray()
    chunk_size = 64 * 1024  # 64 KB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB",
            )

    # 3. Validate non-empty file
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # 4. Ingest and index
    try:
        metadata, is_duplicate = ingestion_service.ingest_document(
            file_bytes=bytes(content),
            original_filename=filename,
        )
    except DocumentParseError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document parsing error: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {str(e)}",
        )

    # 5. Handle duplicate document policy
    if is_duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"Document '{filename}' with identical content has already been indexed.",
                "existing_document_id": metadata.document_id,
                "chunk_count": metadata.chunk_count,
            },
        )

    return DocumentUploadResponse(
        document_id=metadata.document_id,
        filename=metadata.filename,
        status=metadata.status,
        chunk_count=metadata.chunk_count,
        file_size_bytes=metadata.file_size_bytes,
        content_hash=metadata.content_hash,
        message="Document successfully processed and indexed into knowledge base.",
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Indexed Documents",
    description="Retrieve all indexed documents and their metadata.",
)
async def list_documents(
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> DocumentListResponse:
    docs = metadata_repo.list_documents()
    return DocumentListResponse(total=len(docs), documents=docs)


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
    status_code=status.HTTP_200_OK,
    summary="Get Document Details",
    description="Retrieve metadata for a specific document by its unique document ID.",
)
async def get_document(
    document_id: str,
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> DocumentMetadata:
    doc = metadata_repo.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return doc


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Document",
    description="Remove a document, its raw file, and its indexed vector embeddings from the knowledge base.",
)
async def delete_document(
    document_id: str,
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
    ingestion_service: DocumentIngestionService = Depends(get_ingestion_service),
) -> DocumentDeleteResponse:
    doc = metadata_repo.get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    deleted = ingestion_service.delete_document(document_id)
    return DocumentDeleteResponse(
        document_id=document_id,
        deleted=deleted,
        message=f"Document '{doc.filename}' and its embeddings were successfully deleted.",
    )
