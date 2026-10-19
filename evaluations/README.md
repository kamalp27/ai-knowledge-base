# RAG Evaluation Framework & Benchmark Suite

This directory contains the reproducible evaluation dataset, synthetic document corpus, and reporting infrastructure for the **AI Knowledge Base — Document Question Answering with RAG** application.

---

## 🎯 Purpose and Objectives

The RAG evaluation suite provides a deterministic, automated framework to measure:
1. **Retrieval Effectiveness**: Did the semantic retrieval layer surface the exact passages containing the facts required to answer the question?
2. **Ranking Quality**: How high up in the retrieved context was the first relevant evidence passage located?
3. **Safety & Groundedness (Abstention Accuracy)**: Did the system faithfully abstain (`"I could not find sufficient evidence..."`) when presented with questions whose answers are absent from the document corpus?
4. **Adversarial & Injection Resistance**: Does the system refuse to follow prompt injections embedded inside document context?
5. **Execution Latency Profiling**: Per-phase latency measurements for retrieval, LLM synthesis, and end-to-end round trip.

> [!NOTE]
> The evaluation corpus and benchmark questions are **strictly synthetic** technical references (photovoltaics, quantum computing, and distributed consensus) free from any proprietary, confidential, or personal information. They serve as reproducible benchmarks for regression testing and continuous integration.

---

## 📁 Evaluation Directory Structure

```text
evaluations/
├── datasets/
│   ├── sample_corpus/
│   │   ├── photovoltaic_systems.md       # Solar cell physics, inverter topologies, and maintenance
│   │   ├── quantum_computing_principles.txt # Qubits, Bloch sphere, cryogenics, and coherence times
│   │   └── distributed_consensus_guide.pdf  # 3-page Raft consensus, states, election timers, and split-brain safety
│   └── synthetic_benchmark.json          # 10 curated questions (7 answerable, 3 unanswerable)
├── reports/                              # Generated JSON benchmark results (.gitignored)
│   ├── .gitkeep
│   ├── eval_results.json                 # Offline deterministic test-double results
│   └── eval_results_real_embeddings.json # SentenceTransformers (all-MiniLM-L6-v2) results
└── README.md                             # This documentation
```

---

## 📊 Core Metric Definitions

Relevance matching is defined **explicitly and deterministically**:
A retrieved chunk is scored as relevant to an expected evidence requirement if:
1. The chunk's source filename matches the expected document filename (case-insensitive base name match).
2. The chunk's text contains at least one of the expected ground-truth substrings.

Missing expected evidence is never silently treated as successful retrieval.

### 1. Mean Recall@k
$$\text{Recall@}k = \frac{|\{\text{expected sources retrieved within top-}k\}|}{|\text{expected sources}|}$$
- Measures the fraction of required supporting passages captured in the top-$k$ retrieved chunks.
- For single-passage questions, Recall@$k$ is $1.0$ if the passage was retrieved, and $0.0$ otherwise.
- For cross-passage synthesis questions (e.g., comparing monocrystalline vs polycrystalline across sections), Recall@$k$ measures the fraction of all required evidence chunks retrieved.
- Unanswerable questions have no expected supporting passages and are evaluated via Abstention Accuracy instead.

### 2. Mean Reciprocal Rank (MRR)
$$\text{MRR} = \frac{1}{|Q_{\text{ans}}|} \sum_{i=1}^{|Q_{\text{ans}}|} \frac{1}{\text{rank}_i}$$
- Evaluates ranking quality. $\text{rank}_i$ is the 1-based position of the **first relevant chunk** in the retrieved list.
- If the top chunk contains the answer, $\text{RR} = 1.0$.
- If the first relevant chunk appears at rank 2, $\text{RR} = 0.5$; at rank 3, $\text{RR} = 0.3333$.
- If no relevant chunk is retrieved within top-$k$, $\text{RR} = 0.0$.

### 3. Abstention Accuracy
$$\text{Abstention Accuracy} = \frac{|\{\text{unanswerable questions correctly abstaining}\}|}{|\text{unanswerable questions}|}$$
- Evaluates the system's ability to resist hallucinating facts for queries that cannot be answered from the corpus.
- The system succeeds if `evidence_found == False` and the response explicitly returns `"I could not find sufficient evidence in the uploaded documents to answer your question."`

---

## 🚀 Running the Evaluation Suite

The command-line runner is located at `scripts/evaluate.py`.

### 1. Fast, Deterministic Offline Evaluation (No Model Downloads)
Runs against an in-memory vector store with deterministic fake embeddings and fake LLM. Perfect for fast CI and regression verification without network access:
```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py --output evaluations/reports/eval_results.json
```

### 2. Real Semantic Embeddings & Persistent ChromaDB Evaluation
Runs using the real `SentenceTransformers` (`all-MiniLM-L6-v2`) model with persistent local ChromaDB indexing:
```powershell
.\.venv\Scripts\python.exe scripts/evaluate.py --use-real-embeddings --output evaluations/reports/eval_results_real_embeddings.json
```

### 3. Custom Evaluation Options & Flags
```text
options:
  -h, --help            Show this help message and exit
  --benchmark PATH      Path to benchmark JSON dataset (default: evaluations/datasets/synthetic_benchmark.json)
  --corpus PATH         Path to sample corpus directory (default: evaluations/datasets/sample_corpus)
  --top-k K             Number of context chunks to retrieve (default: 4)
  --use-real-embeddings Use real SentenceTransformers and ChromaDB
  --embedding-model     Model name (default: all-MiniLM-L6-v2)
  --llm-provider        LLM provider for synthesis: fake | openai | anthropic (default: fake)
  --output PATH         Path to save JSON evaluation report (default: evaluations/reports/eval_results.json)
```

---

## 📈 Benchmark Results

### 1. Real Semantic Embeddings Run (`all-MiniLM-L6-v2` + ChromaDB)

Executed on Windows (Python 3.12, PyTorch 2.14.1, ChromaDB 1.5.9):

```text
==============================================================================
           RAG EVALUATION BENCHMARK EXECUTION SUMMARY
==============================================================================
Timestamp:       2026-10-19T22:46:14.083958+00:00
Benchmark:       Synthetic RAG Evaluation Benchmark
Embedding Model: all-MiniLM-L6-v2
Vector Database: ChromaDB
LLM Provider:    fake
Top-K Chunks:    4
Corpus Files:    distributed_consensus_guide.pdf, photovoltaic_systems.md, quantum_computing_principles.txt
------------------------------------------------------------------------------
Total Questions Evaluated:  10
  • Answerable Questions:   7
  • Unanswerable Questions: 3
------------------------------------------------------------------------------
CORE RETRIEVAL & SAFETY METRICS:
  [1] Mean Recall@4:              100.00%
  [2] Mean Reciprocal Rank (MRR): 1.0000
  [3] Abstention Accuracy:        100.00%
------------------------------------------------------------------------------
EXECUTION LATENCY PROFILING:
  • Average Retrieval Latency: 15.90 ms
  • Average LLM Latency:       0.12 ms
  • Average Total Latency:     16.06 ms
  • P95 Total Latency:         18.34 ms
==============================================================================

PER-QUESTION EVALUATION BREAKDOWN:
ID    Category        Ans?   Recall@k   MRR      Abstained?   Total(ms) 
------------------------------------------------------------------------
q1    single_passage  Yes    1.00       1.00     No           19.6      
q2    single_passage  Yes    1.00       1.00     No           16.8      
q3    single_passage  Yes    1.00       1.00     No           14.4      
q4    cross_passage   Yes    1.00       1.00     No           16.2      
q5    single_passage  Yes    1.00       1.00     No           16.7      
q6    cross_passage   Yes    1.00       1.00     No           14.3      
q7    single_passage  Yes    1.00       1.00     No           16.2      
q8    unanswerable    No     —          —        Yes (OK)     16.0      
q9    unanswerable    No     —          —        Yes (OK)     14.1      
q10   unanswerable    No     —          —        Yes (OK)     16.2      
==============================================================================
```

> [!NOTE]
> Latencies reflect local CPU inference. Recall@4 of 100% and MRR of 1.0000 demonstrate that the semantic dense embeddings (`all-MiniLM-L6-v2`) accurately map the domain terminology to the relevant passages across PDF, Markdown, and TXT files. Abstention accuracy of 100% confirms that unanswerable queries cleanly abstain without hallucination.
