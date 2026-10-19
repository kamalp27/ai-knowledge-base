"""RAG evaluation and benchmarking package."""
from backend.app.rag.evaluation.metrics import (
    EvaluationMetrics,
    QueryEvaluationResult,
    calculate_recall_at_k,
    calculate_mrr,
    is_chunk_relevant,
)

__all__ = [
    "EvaluationMetrics",
    "QueryEvaluationResult",
    "calculate_recall_at_k",
    "calculate_mrr",
    "is_chunk_relevant",
]
