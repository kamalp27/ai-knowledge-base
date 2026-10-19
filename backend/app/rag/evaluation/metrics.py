from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.models.query import RetrievedChunk


class ExpectedSource(BaseModel):
    """Schema for an expected evidence source in benchmark questions."""
    document_filename: str
    expected_substrings: List[str]


def is_chunk_relevant(chunk: RetrievedChunk, expected_source: ExpectedSource) -> bool:
    """Determine deterministically whether a retrieved chunk matches expected source evidence.
    
    A chunk is relevant if:
    1. Its filename matches expected source document filename (case-insensitive base name match).
    2. The chunk's text contains at least one of the expected substrings (case-insensitive).
    """
    chunk_fname = chunk.filename.strip().lower()
    exp_fname = expected_source.document_filename.strip().lower()

    if chunk_fname != exp_fname:
        return False

    chunk_text = chunk.text.lower()
    for sub in expected_source.expected_substrings:
        if sub.lower() in chunk_text:
            return True

    return False


def calculate_recall_at_k(
    retrieved_chunks: List[RetrievedChunk],
    expected_sources: List[ExpectedSource],
    k: int,
) -> float:
    """Calculate Recall@k: fraction of expected supporting passages retrieved within top-k chunks.
    
    If expected_sources is empty, returns 0.0 (unanswerable questions do not use retrieval recall).
    """
    if not expected_sources:
        return 0.0

    top_k_chunks = retrieved_chunks[:k]
    matched_sources = 0

    for exp_source in expected_sources:
        found = any(is_chunk_relevant(c, exp_source) for c in top_k_chunks)
        if found:
            matched_sources += 1

    return round(matched_sources / len(expected_sources), 4)


def calculate_mrr(
    retrieved_chunks: List[RetrievedChunk],
    expected_sources: List[ExpectedSource],
) -> float:
    """Calculate Reciprocal Rank (RR): reciprocal of the 1-based rank of the first relevant chunk.
    
    Returns 0.0 if no relevant chunk is retrieved or if expected_sources is empty.
    """
    if not expected_sources:
        return 0.0

    for rank, chunk in enumerate(retrieved_chunks, start=1):
        for exp in expected_sources:
            if is_chunk_relevant(chunk, exp):
                return round(1.0 / rank, 4)

    return 0.0


class QueryEvaluationResult(BaseModel):
    """Evaluation result for an individual benchmark question."""
    question_id: str
    question: str
    category: str
    is_answerable: bool
    recall_at_k: float = Field(..., description="Fraction of expected supporting sources in top-k")
    reciprocal_rank: float = Field(..., description="Reciprocal rank (1/rank) of first relevant chunk")
    abstained: bool = Field(..., description="Whether system correctly abstained")
    abstention_accurate: Optional[bool] = Field(None, description="For unanswerable queries: whether abstention was correct")
    citations_count: int
    retrieved_count: int
    retrieval_time_ms: float
    llm_time_ms: float
    total_time_ms: float
    answer_preview: str


class EvaluationMetrics(BaseModel):
    """Aggregated evaluation metrics across the benchmark run."""
    total_queries: int
    answerable_queries: int
    unanswerable_queries: int
    mean_recall_at_k: float = Field(..., description="Average Recall@k across answerable queries")
    mean_reciprocal_rank: float = Field(..., description="Mean Reciprocal Rank (MRR) across answerable queries")
    abstention_accuracy: float = Field(..., description="Accuracy of abstaining on unanswerable queries")
    avg_retrieval_latency_ms: float
    avg_llm_latency_ms: float
    avg_total_latency_ms: float
    p95_total_latency_ms: float
