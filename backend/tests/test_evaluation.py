import json
import os
import pytest
from backend.app.models.query import RetrievedChunk
from backend.app.rag.evaluation.metrics import (
    ExpectedSource,
    calculate_mrr,
    calculate_recall_at_k,
    is_chunk_relevant,
)
from backend.app.rag.evaluation.runner import RAGEvaluationRunner


def test_is_chunk_relevant_matching():
    expected = ExpectedSource(
        document_filename="photovoltaic_systems.md",
        expected_substrings=["Monocrystalline Silicon", "20.0% to 24.5%"],
    )

    # Matching chunk
    chunk_match = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        filename="photovoltaic_systems.md",
        page_number=1,
        text="Monocrystalline Silicon cells achieve high efficiency.",
        score=0.9,
    )
    assert is_chunk_relevant(chunk_match, expected) is True

    # Different filename
    chunk_wrong_file = RetrievedChunk(
        chunk_id="c2",
        document_id="d2",
        filename="other_systems.md",
        page_number=1,
        text="Monocrystalline Silicon cells achieve high efficiency.",
        score=0.9,
    )
    assert is_chunk_relevant(chunk_wrong_file, expected) is False

    # Same filename, but missing expected substring
    chunk_wrong_content = RetrievedChunk(
        chunk_id="c3",
        document_id="d1",
        filename="photovoltaic_systems.md",
        page_number=1,
        text="Solar energy harnesses electromagnetic radiation.",
        score=0.8,
    )
    assert is_chunk_relevant(chunk_wrong_content, expected) is False


def test_recall_at_k_calculation():
    exp1 = ExpectedSource(
        document_filename="doc_a.txt",
        expected_substrings=["Topic Alpha"],
    )
    exp2 = ExpectedSource(
        document_filename="doc_b.txt",
        expected_substrings=["Topic Beta"],
    )

    chunk1 = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        filename="doc_a.txt",
        text="Contains Topic Alpha details.",
        score=0.95,
    )
    chunk2 = RetrievedChunk(
        chunk_id="c2",
        document_id="d2",
        filename="doc_other.txt",
        text="Irrelevant passage.",
        score=0.85,
    )
    chunk3 = RetrievedChunk(
        chunk_id="c3",
        document_id="d3",
        filename="doc_b.txt",
        text="Contains Topic Beta information.",
        score=0.75,
    )

    retrieved = [chunk1, chunk2, chunk3]

    # At k=1, only exp1 is retrieved (1 / 2 = 0.5)
    assert calculate_recall_at_k(retrieved, [exp1, exp2], k=1) == 0.5

    # At k=2, still only exp1 (1 / 2 = 0.5)
    assert calculate_recall_at_k(retrieved, [exp1, exp2], k=2) == 0.5

    # At k=3, both exp1 and exp2 are retrieved (2 / 2 = 1.0)
    assert calculate_recall_at_k(retrieved, [exp1, exp2], k=3) == 1.0


def test_mrr_calculation():
    exp = ExpectedSource(
        document_filename="doc_a.txt",
        expected_substrings=["Target Fact"],
    )

    irrelevant = RetrievedChunk(
        chunk_id="c0",
        document_id="d0",
        filename="doc_x.txt",
        text="Not related.",
        score=0.9,
    )
    relevant = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        filename="doc_a.txt",
        text="Contains Target Fact precisely.",
        score=0.8,
    )

    # First relevant at rank 1 -> RR = 1.0
    assert calculate_mrr([relevant, irrelevant], [exp]) == 1.0

    # First relevant at rank 2 -> RR = 0.5
    assert calculate_mrr([irrelevant, relevant], [exp]) == 0.5

    # No relevant chunks -> RR = 0.0
    assert calculate_mrr([irrelevant], [exp]) == 0.0

    # Empty expected sources -> RR = 0.0
    assert calculate_mrr([relevant], []) == 0.0


def test_evaluation_runner_end_to_end(tmp_path):
    report_file = tmp_path / "test_eval_report.json"

    runner = RAGEvaluationRunner(
        corpus_dir="evaluations/datasets/sample_corpus",
        benchmark_file="evaluations/datasets/synthetic_benchmark.json",
        top_k=4,
        use_real_embeddings=False,  # Deterministic fake embeddings for fast test
        llm_provider_type="fake",
        output_report_path=str(report_file),
    )

    report = runner.run_evaluation()

    assert report.benchmark_name == "Synthetic RAG Evaluation Benchmark"
    assert report.metrics.total_queries == 10
    assert report.metrics.answerable_queries == 7
    assert report.metrics.unanswerable_queries == 3

    # Metrics should be valid numbers between 0 and 1
    assert 0.0 <= report.metrics.mean_recall_at_k <= 1.0
    assert 0.0 <= report.metrics.mean_reciprocal_rank <= 1.0
    assert report.metrics.abstention_accuracy == 1.0  # FakeLLM abstains on empty/unanswerable

    # Verify JSON report file was generated
    assert report_file.exists()
    with open(report_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["metrics"]["total_queries"] == 10
    assert "query_results" in saved_data
    assert len(saved_data["query_results"]) == 10


def test_evaluation_runner_missing_files_error():
    runner_missing_bench = RAGEvaluationRunner(
        corpus_dir="evaluations/datasets/sample_corpus",
        benchmark_file="nonexistent_bench.json",
    )
    with pytest.raises(FileNotFoundError):
        runner_missing_bench.run_evaluation()

    runner_missing_corpus = RAGEvaluationRunner(
        corpus_dir="nonexistent_corpus_dir",
        benchmark_file="evaluations/datasets/synthetic_benchmark.json",
    )
    with pytest.raises(FileNotFoundError):
        runner_missing_corpus.run_evaluation()
