from datetime import datetime, timezone
import json
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from backend.app.core.config import Settings
from backend.app.models.query import QueryRequest
from backend.app.rag.embeddings import (
    BaseEmbeddingService,
    DeterministicFakeEmbeddingService,
    SentenceTransformerEmbeddingService,
)
from backend.app.rag.evaluation.metrics import (
    EvaluationMetrics,
    ExpectedSource,
    QueryEvaluationResult,
    calculate_mrr,
    calculate_recall_at_k,
)
from backend.app.rag.ingestion import DocumentIngestionService
from backend.app.rag.llm import BaseLLMProvider, FakeLLMProvider, get_llm_provider
from backend.app.rag.metadata_repository import MetadataRepository
from backend.app.rag.query_service import QueryService
from backend.app.rag.retrieval import RetrievalService
from backend.app.rag.vector_store import (
    BaseVectorStore,
    ChromaVectorStore,
    InMemoryVectorStore,
)


class BenchmarkRunReport(BaseModel):
    """Complete machine-readable evaluation report schema."""
    timestamp: str
    benchmark_name: str
    config: Dict[str, Any]
    metrics: EvaluationMetrics
    query_results: List[QueryEvaluationResult]


class RAGEvaluationRunner:
    """Orchestrates end-to-end RAG evaluation runs."""

    def __init__(
        self,
        corpus_dir: str,
        benchmark_file: str,
        top_k: int = 4,
        use_real_embeddings: bool = False,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        llm_provider_type: str = "fake",
        output_report_path: Optional[str] = None,
    ):
        self.corpus_dir = corpus_dir
        self.benchmark_file = benchmark_file
        self.top_k = top_k
        self.use_real_embeddings = use_real_embeddings
        self.embedding_model_name = embedding_model_name
        self.llm_provider_type = llm_provider_type
        self.output_report_path = output_report_path

    def run_evaluation(self) -> BenchmarkRunReport:
        """Execute evaluation suite and return complete benchmark run report."""
        if not os.path.exists(self.benchmark_file):
            raise FileNotFoundError(f"Benchmark file not found: {self.benchmark_file}")
        if not os.path.isdir(self.corpus_dir):
            raise FileNotFoundError(f"Corpus directory not found: {self.corpus_dir}")

        with open(self.benchmark_file, "r", encoding="utf-8") as f:
            benchmark_data = json.load(f)

        questions = benchmark_data.get("questions", [])
        if not questions:
            raise ValueError("Benchmark dataset contains no questions.")

        # Setup isolated temporary staging directory for evaluation run
        temp_work_dir = tempfile.mkdtemp(prefix="rag_eval_run_")
        try:
            temp_db_path = os.path.join(temp_work_dir, "eval_metadata.db")
            temp_raw_docs = os.path.join(temp_work_dir, "raw_docs")
            temp_chroma = os.path.join(temp_work_dir, "chroma")
            os.makedirs(temp_raw_docs, exist_ok=True)

            metadata_repo = MetadataRepository(db_path=temp_db_path)

            if self.use_real_embeddings:
                embedding_service: BaseEmbeddingService = SentenceTransformerEmbeddingService(
                    model_name=self.embedding_model_name
                )
                vector_store: BaseVectorStore = ChromaVectorStore(
                    persist_directory=temp_chroma,
                    collection_name="eval_collection",
                )
            else:
                embedding_service = DeterministicFakeEmbeddingService(dimension=32)
                vector_store = InMemoryVectorStore()

            # LLM provider
            if self.llm_provider_type == "fake":
                llm_provider: BaseLLMProvider = FakeLLMProvider()
            else:
                eval_settings = Settings(LLM_PROVIDER=self.llm_provider_type)
                llm_provider = get_llm_provider(eval_settings)

            # Ingestion Service
            ingestion_service = DocumentIngestionService(
                raw_documents_dir=temp_raw_docs,
                chunk_size=1000,
                chunk_overlap=200,
                metadata_repo=metadata_repo,
                embedding_service=embedding_service,
                vector_store=vector_store,
            )

            # 1. Ingest corpus documents
            corpus_files = [
                f for f in os.listdir(self.corpus_dir)
                if os.path.isfile(os.path.join(self.corpus_dir, f))
            ]
            for fname in corpus_files:
                fpath = os.path.join(self.corpus_dir, fname)
                with open(fpath, "rb") as f:
                    file_bytes = f.read()
                ingestion_service.ingest_document(
                    file_bytes=file_bytes,
                    original_filename=fname,
                )

            # 2. Setup Query & Retrieval Services
            retrieval_service = RetrievalService(
                embedding_service=embedding_service,
                vector_store=vector_store,
                similarity_threshold=0.0,
            )
            query_service = QueryService(
                retrieval_service=retrieval_service,
                llm_provider=llm_provider,
            )

            # 3. Evaluate Questions
            query_results: List[QueryEvaluationResult] = []
            answerable_recalls: List[float] = []
            answerable_mrrs: List[float] = []
            abstention_accuracies: List[float] = []
            retrieval_latencies: List[float] = []
            llm_latencies: List[float] = []
            total_latencies: List[float] = []

            for q_item in questions:
                q_id = q_item["id"]
                question = q_item["question"]
                category = q_item.get("category", "general")
                is_answerable = q_item.get("is_answerable", True)

                expected_sources = [
                    ExpectedSource(**src)
                    for src in q_item.get("expected_sources", [])
                ]

                # Run query
                q_req = QueryRequest(question=question, top_k=self.top_k)
                response = query_service.answer_query(q_req, default_top_k=self.top_k)

                retrieval_latencies.append(response.timing.retrieval_time_ms)
                llm_latencies.append(response.timing.llm_time_ms)
                total_latencies.append(response.timing.total_time_ms)

                abstained = (
                    not response.evidence_found
                    or "could not find sufficient evidence" in response.answer.lower()
                    or "insufficient evidence" in response.answer.lower()
                )

                if is_answerable:
                    recall_k = calculate_recall_at_k(response.retrieved_chunks, expected_sources, self.top_k)
                    rr = calculate_mrr(response.retrieved_chunks, expected_sources)
                    abstention_accurate = None
                    answerable_recalls.append(recall_k)
                    answerable_mrrs.append(rr)
                else:
                    recall_k = 0.0
                    rr = 0.0
                    abstention_accurate = abstained
                    abstention_accuracies.append(1.0 if abstained else 0.0)

                query_results.append(
                    QueryEvaluationResult(
                        question_id=q_id,
                        question=question,
                        category=category,
                        is_answerable=is_answerable,
                        recall_at_k=recall_k,
                        reciprocal_rank=rr,
                        abstained=abstained,
                        abstention_accurate=abstention_accurate,
                        citations_count=len(response.citations),
                        retrieved_count=len(response.retrieved_chunks),
                        retrieval_time_ms=response.timing.retrieval_time_ms,
                        llm_time_ms=response.timing.llm_time_ms,
                        total_time_ms=response.timing.total_time_ms,
                        answer_preview=response.answer[:120],
                    )
                )

            # 4. Compute Aggregate Metrics
            mean_recall = round(float(np.mean(answerable_recalls)), 4) if answerable_recalls else 0.0
            mean_mrr = round(float(np.mean(answerable_mrrs)), 4) if answerable_mrrs else 0.0
            abstention_acc = round(float(np.mean(abstention_accuracies)), 4) if abstention_accuracies else 0.0

            avg_retrieval = round(float(np.mean(retrieval_latencies)), 2) if retrieval_latencies else 0.0
            avg_llm = round(float(np.mean(llm_latencies)), 2) if llm_latencies else 0.0
            avg_total = round(float(np.mean(total_latencies)), 2) if total_latencies else 0.0
            p95_total = round(float(np.percentile(total_latencies, 95)), 2) if total_latencies else 0.0

            metrics = EvaluationMetrics(
                total_queries=len(questions),
                answerable_queries=len(answerable_recalls),
                unanswerable_queries=len(abstention_accuracies),
                mean_recall_at_k=mean_recall,
                mean_reciprocal_rank=mean_mrr,
                abstention_accuracy=abstention_acc,
                avg_retrieval_latency_ms=avg_retrieval,
                avg_llm_latency_ms=avg_llm,
                avg_total_latency_ms=avg_total,
                p95_total_latency_ms=p95_total,
            )

            config_meta = {
                "top_k": self.top_k,
                "use_real_embeddings": self.use_real_embeddings,
                "embedding_model": self.embedding_model_name if self.use_real_embeddings else "DeterministicFakeEmbeddingService(dim=32)",
                "vector_store": "ChromaDB" if self.use_real_embeddings else "InMemoryVectorStore",
                "llm_provider": self.llm_provider_type,
                "corpus_files": corpus_files,
            }

            report = BenchmarkRunReport(
                timestamp=datetime.now(timezone.utc).isoformat(),
                benchmark_name=benchmark_data.get("benchmark_metadata", {}).get("name", "RAG Benchmark"),
                config=config_meta,
                metrics=metrics,
                query_results=query_results,
            )

            # 5. Export JSON report if requested
            if self.output_report_path:
                out_dir = os.path.dirname(os.path.abspath(self.output_report_path))
                if out_dir:
                    os.makedirs(out_dir, exist_ok=True)
                with open(self.output_report_path, "w", encoding="utf-8") as f:
                    f.write(report.model_dump_json(indent=2))

            return report

        finally:
            # Cleanup temporary working directory
            shutil.rmtree(temp_work_dir, ignore_errors=True)
