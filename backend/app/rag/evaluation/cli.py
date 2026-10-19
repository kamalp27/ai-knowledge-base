import argparse
import sys
from backend.app.rag.evaluation.runner import RAGEvaluationRunner


def print_terminal_summary(report):
    """Print clean, formatted terminal summary table of benchmark results."""
    m = report.metrics
    c = report.config

    print("\n" + "=" * 78)
    print("           RAG EVALUATION BENCHMARK EXECUTION SUMMARY")
    print("=" * 78)
    print(f"Timestamp:       {report.timestamp}")
    print(f"Benchmark:       {report.benchmark_name}")
    print(f"Embedding Model: {c.get('embedding_model')}")
    print(f"Vector Database: {c.get('vector_store')}")
    print(f"LLM Provider:    {c.get('llm_provider')}")
    print(f"Top-K Chunks:    {c.get('top_k')}")
    print(f"Corpus Files:    {', '.join(c.get('corpus_files', []))}")
    print("-" * 78)

    print(f"Total Questions Evaluated:  {m.total_queries}")
    print(f"  • Answerable Questions:   {m.answerable_queries}")
    print(f"  • Unanswerable Questions: {m.unanswerable_queries}")
    print("-" * 78)

    print("CORE RETRIEVAL & SAFETY METRICS:")
    print(f"  [1] Mean Recall@{c.get('top_k')}:       {m.mean_recall_at_k * 100:.2f}%")
    print(f"  [2] Mean Reciprocal Rank (MRR): {m.mean_reciprocal_rank:.4f}")
    print(f"  [3] Abstention Accuracy:        {m.abstention_accuracy * 100:.2f}%")
    print("-" * 78)

    print("EXECUTION LATENCY PROFILING:")
    print(f"  • Average Retrieval Latency: {m.avg_retrieval_latency_ms:.2f} ms")
    print(f"  • Average LLM Latency:       {m.avg_llm_latency_ms:.2f} ms")
    print(f"  • Average Total Latency:     {m.avg_total_latency_ms:.2f} ms")
    print(f"  • P95 Total Latency:         {m.p95_total_latency_ms:.2f} ms")
    print("=" * 78)

    print("\nPER-QUESTION EVALUATION BREAKDOWN:")
    header = f"{'ID':<5} {'Category':<15} {'Ans?':<6} {'Recall@k':<10} {'MRR':<8} {'Abstained?':<12} {'Total(ms)':<10}"
    print(header)
    print("-" * len(header))

    for r in report.query_results:
        ans_str = "Yes" if r.is_answerable else "No"
        rec_str = f"{r.recall_at_k:.2f}" if r.is_answerable else "—"
        mrr_str = f"{r.reciprocal_rank:.2f}" if r.is_answerable else "—"
        abs_str = "Yes (OK)" if (r.abstained and not r.is_answerable) else "Yes" if r.abstained else "No"
        print(f"{r.question_id:<5} {r.category:<15} {ans_str:<6} {rec_str:<10} {mrr_str:<8} {abs_str:<12} {r.total_time_ms:<10.1f}")

    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="CLI Evaluation Runner for AI Knowledge Base RAG Pipeline."
    )
    parser.add_argument(
        "--benchmark",
        default="evaluations/datasets/synthetic_benchmark.json",
        help="Path to benchmark JSON dataset file (default: evaluations/datasets/synthetic_benchmark.json)",
    )
    parser.add_argument(
        "--corpus",
        default="evaluations/datasets/sample_corpus",
        help="Path to directory containing reference corpus documents (default: evaluations/datasets/sample_corpus)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Number of context chunks to retrieve (default: 4)",
    )
    parser.add_argument(
        "--use-real-embeddings",
        action="store_true",
        help="Use real SentenceTransformers and ChromaDB instead of deterministic fake embeddings",
    )
    parser.add_argument(
        "--embedding-model",
        default="all-MiniLM-L6-v2",
        help="SentenceTransformers model name (default: all-MiniLM-L6-v2)",
    )
    parser.add_argument(
        "--llm-provider",
        default="fake",
        choices=["fake", "openai", "anthropic"],
        help="LLM provider for synthesis (default: fake for deterministic reproducible tests)",
    )
    parser.add_argument(
        "--output",
        default="evaluations/reports/eval_results.json",
        help="Path to save machine-readable JSON evaluation report (default: evaluations/reports/eval_results.json)",
    )

    args = parser.parse_args()

    try:
        runner = RAGEvaluationRunner(
            corpus_dir=args.corpus,
            benchmark_file=args.benchmark,
            top_k=args.top_k,
            use_real_embeddings=args.use_real_embeddings,
            embedding_model_name=args.embedding_model,
            llm_provider_type=args.llm_provider,
            output_report_path=args.output,
        )

        report = runner.run_evaluation()
        print_terminal_summary(report)

        if args.output:
            print(f"Machine-readable JSON report written to: {args.output}\n")

        sys.exit(0)

    except Exception as e:
        print(f"\n[FATAL ERROR] Evaluation run failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
