from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema for incoming semantic query request."""

    question: str = Field(..., min_length=1, description="Question text to answer from documents")
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Override top_k retrieval count")


class Citation(BaseModel):
    """Source citation identifying document and page."""

    document_id: str = Field(..., description="Source document identifier")
    filename: str = Field(..., description="Source document filename")
    page_number: Optional[int] = Field(default=None, description="Page number if applicable")
    chunk_id: str = Field(..., description="Chunk identifier")
    snippet: str = Field(..., description="Excerpt of referenced context")


class RetrievedChunk(BaseModel):
    """Detailed chunk retrieved from vector store."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    filename: str = Field(..., description="Source document filename")
    page_number: Optional[int] = Field(default=None, description="Page number if available")
    text: str = Field(..., description="Raw text content of the chunk")
    score: float = Field(..., description="Similarity or relevance score")


class TimingInfo(BaseModel):
    """Execution timing breakdown in milliseconds."""

    retrieval_time_ms: float = Field(..., description="Time taken to retrieve and score chunks")
    llm_time_ms: float = Field(..., description="Time taken to generate the answer via LLM")
    total_time_ms: float = Field(..., description="Total end-to-end request latency")


class QueryResponse(BaseModel):
    """Schema for question-answering result."""

    question: str = Field(..., description="Original question submitted")
    answer: str = Field(..., description="Generated answer grounded solely in retrieved context")
    citations: List[Citation] = Field(default_factory=list, description="List of source citations")
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list, description="Retrieved context chunks")
    timing: TimingInfo = Field(..., description="Execution latency breakdown")
    evidence_found: bool = Field(..., description="Whether sufficient evidence was found in the indexed corpus")
