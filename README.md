# AI Knowledge Base — Document Question Answering with RAG

A production-ready, enterprise-grade AI Knowledge Base application featuring Retrieval-Augmented Generation (RAG) for multi-document question answering. Built with a modular **FastAPI** Python backend, **ChromaDB** vector storage, **Sentence Transformers** dense embeddings, and **React 18 + TypeScript + Vite** frontend.

---

## 📁 Project Structure

```text
ai-knowledge-base/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app with CORS, lifespan, /health & /ready
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py           # /api/v1 router aggregation
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── health.py       # Health & readiness probe handlers
│   │   │           ├── documents.py    # Document upload, list, get, and delete endpoints
│   │   │           └── query.py        # Semantic RAG query endpoint with grounded prompt
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py               # Pydantic Settings & environment config
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── health.py               # Health & Readiness Pydantic schemas
│   │   │   ├── documents.py            # Document metadata and upload/delete schemas
│   │   │   └── query.py                # Query, citation, retrieved chunk, and timing schemas
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── parser.py               # PyMuPDF PDF, Markdown, and TXT page-by-page extractor
│   │   │   ├── chunker.py              # Configurable text chunker preserving page provenance
│   │   │   ├── embeddings.py           # SentenceTransformer and DeterministicFake embeddings
│   │   │   ├── vector_store.py         # Persistent ChromaDB and in-memory vector stores
│   │   │   ├── metadata_repository.py  # SQLite repository for document metadata
│   │   │   ├── retrieval.py            # Semantic retrieval service with similarity scoring
│   │   │   ├── llm.py                  # LLM providers (OpenAI, Anthropic, Fake) & safety guards
│   │   │   ├── query_service.py        # Context assembly, citation tracing, and timing
│   │   │   ├── ingestion.py            # Upload pipeline, duplicate check, and atomic storage
│   │   │   ├── dependencies.py         # FastAPI dependency injection container
│   │   │   └── evaluation/             # RAG evaluation metrics and benchmark runner
│   │   │       ├── __init__.py
│   │   │       ├── metrics.py          # Recall@k, MRR, and Abstention Accuracy calculations
│   │   │       ├── runner.py           # Evaluation pipeline orchestrator and latency profiler
│   │   │       └── cli.py              # Terminal summary table and CLI argument parsing
│   │   └── services/
│   │       └── __init__.py             # Business logic services
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Pytest fixtures with fast test-doubles & temp paths
│   │   ├── test_health.py              # Health and readiness endpoint tests
│   │   ├── test_parser.py              # PDF, Markdown, and TXT parser unit tests
│   │   ├── test_chunker.py             # Sliding window and overlap chunking tests
│   │   ├── test_embeddings_and_vector_store.py # Vector store, embeddings, and SQLite tests
│   │   ├── test_documents_api.py       # Upload, duplicate check, list, get, delete API tests
│   │   ├── test_query_api.py           # Semantic query, citation, injection defense tests
│   │   └── test_evaluation.py          # Metrics and evaluation runner tests
│   └── requirements.txt                # Backend dependencies
├── frontend/
│   ├── index.html                      # Frontend HTML shell
│   ├── package.json                    # React 18, TypeScript & Vite configuration
│   ├── tsconfig.json                   # TypeScript compiler options
│   ├── tsconfig.node.json              # TypeScript Vite configuration
│   ├── vite.config.ts                  # Vite config with backend proxy
│   ├── .env.example                    # Frontend environment template
│   └── src/
│       ├── main.tsx                    # React application entrypoint
│       ├── App.tsx                     # Main layout & live health dashboard
│       ├── App.css                     # Component styling
│       ├── index.css                   # Global theme
│       ├── vite-env.d.ts               # Environment typings
│       ├── components/
│       │   ├── HealthStatus.tsx        # System health & readiness status card
│       │   ├── DocumentUpload.tsx      # Drag-and-drop document upload with validation
│       │   ├── DocumentLibrary.tsx     # Document list, metadata inspection, and delete
│       │   └── QuestionAnswering.tsx   # Chat-style query interface with grounded citations
│       ├── services/
│       │   └── api.ts                  # Axios client for backend endpoints
│       ├── test/
│       │   ├── setup.ts                # Vitest DOM configuration
│       │   ├── DocumentUpload.test.tsx # Upload component tests
│       │   ├── DocumentLibrary.test.tsx# Library component tests
│       │   └── QuestionAnswering.test.tsx # Query component tests
│       └── types/
│           └── index.ts                # TypeScript data interfaces
├── data/
│   ├── raw_documents/                  # Staging for user documents (.gitignored)
│   ├── vector_store/                   # Persistent vector DB data (.gitignored)
│   └── eval_datasets/                  # Evaluation benchmarks (.gitignored)
├── docs/
│   └── architecture.md                # System design documentation
├── evaluations/
│   ├── datasets/
│   │   ├── sample_corpus/              # Synthetic PDF, Markdown, and TXT documents
│   │   └── synthetic_benchmark.json    # 10 curated benchmark questions & expected evidence
│   ├── reports/                        # Machine-readable evaluation JSON reports
│   └── README.md                       # Evaluation methodology and metrics guide
├── scripts/
│   ├── evaluate.py                     # CLI benchmark evaluation runner
│   ├── run_backend.bat                 # Windows one-click script for backend
│   ├── run_frontend.bat                # Windows one-click script for frontend
│   └── run_tests.bat                   # Windows one-click script for pytest
├── .env.example                        # Template with app, storage & RAG settings
├── .gitignore                          # Excludes secrets, documents, and vector DB
├── pytest.ini                          # Pytest discovery and pythonpath configuration
├── requirements.txt                    # Root shortcut pointing to backend requirements
└── README.md                           # Project documentation
```

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Root system health check |
| `GET` | `/ready` | Root storage and dependency readiness check |
| `GET` | `/api/v1/health` | API v1 health status |
| `GET` | `/api/v1/ready` | API v1 readiness status |
| `POST` | `/api/v1/documents/upload` | Upload & index PDF, TXT, or Markdown documents |
| `GET` | `/api/v1/documents` | List all indexed documents with metadata |
| `GET` | `/api/v1/documents/{document_id}` | Retrieve metadata for a specific document |
| `DELETE` | `/api/v1/documents/{document_id}` | Delete document file, SQLite record, and vector embeddings |
| `POST` | `/api/v1/query` | Semantic similarity query returning grounded answer, citations & timing |

---

## 🔒 Security & Git Hygiene

- **Secrets & Keys**: `.env`, `.env.*`, API keys, private certificates are strictly excluded by `.gitignore`.
- **Private Documents**: `data/raw_documents/*` are gitignored to prevent accidental commits of confidential files.
- **Vector Indexes & Embeddings**: `data/vector_store/*` and SQLite databases (`*.db`, `*.sqlite3`) are gitignored.
- **Untrusted Input Protection**: Document chunks are strictly delimited within system prompts to neutralize adversarial prompt injection attempts (e.g. "Ignore previous instructions").
- **Grounded Answering & Hallucination Defense**: Models are instructed to abstain ("I could not find sufficient evidence...") whenever reference context is insufficient.

---

## 🚀 Getting Started (Windows)

### Prerequisites
- **Python 3.10+** (tested on Python 3.12)
- **Node.js 18+** & **npm** (tested on Node v24, npm 11)

### Setup & Startup
1. **Clone or Navigate to the Workspace**:
   ```powershell
   cd C:\Users\HP\.gemini\antigravity\scratch\ai-knowledge-base
   ```

2. **Configure Environment Variables**:
   ```powershell
   Copy-Item .env.example .env
   ```
   *Edit `.env` to set `LLM_PROVIDER=openai` (or `anthropic`, `fake`) and provide your API key.*

3. **Backend Setup**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pytest backend/tests -v
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Frontend Setup**:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

5. **Running RAG Evaluation Suite**:
   ```powershell
   # Fast offline deterministic benchmark (in-memory, test-doubles)
   .\.venv\Scripts\python.exe scripts/evaluate.py

   # Full semantic evaluation with SentenceTransformers and persistent ChromaDB
   .\.venv\Scripts\python.exe scripts/evaluate.py --use-real-embeddings --output evaluations/reports/custom_eval.json
   ```

- **Backend API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Frontend App**: [http://localhost:5173](http://localhost:5173)

---

## 🚢 Production Deployment

### 1. Docker Deployment
The backend includes a production-hardened `Dockerfile` running Python 3.12-slim as an unprivileged user (`appuser`), featuring dynamic `$PORT` binding and native container health checks.

```bash
# Build the backend image
docker build -t ai-knowledge-base-backend .

# Run container with persistent host storage mounted to /app/data
docker run -d \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e CORS_ORIGINS="https://my-frontend.example.com" \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_KEY="your-secret-api-key" \
  -v $(pwd)/data:/app/data \
  --name ai-knowledge-base \
  ai-knowledge-base-backend
```

### 2. Render Blueprint Deployment (`render.yaml`)
The project includes a ready-to-use `render.yaml` specification describing:
- **Backend Web Service**: Docker runtime with a 1 GB persistent disk mounted at `/app/data` to persist SQLite metadata and ChromaDB embeddings.
- **Frontend Static Site**: Vite static build deployed to Render's global CDN.

**Deployment Steps on Render:**
1. Push this repository to GitHub or GitLab.
2. Log in to the [Render Dashboard](https://dashboard.render.com).
3. Click **New +** > **Blueprint** and connect your repository.
4. Render detects `render.yaml` and provisions both services.
5. In the Render Dashboard under backend **Environment**:
   - Set `LLM_PROVIDER` to `openai` (or `anthropic`).
   - Add your secret `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`).
6. Once both services are active:
   - Copy the deployed frontend URL (e.g. `https://ai-knowledge-base-frontend.onrender.com`) and update `CORS_ORIGINS` in the backend environment.
   - Copy the deployed backend URL (e.g. `https://ai-knowledge-base-backend.onrender.com/api/v1`) and verify `VITE_API_BASE_URL` in the frontend environment, then trigger a frontend rebuild.

> [!IMPORTANT]
> **Persistent Disk Limitations:**
> Persistent disk mounts require a paid Render instance (Starter plan or higher). On free-tier containers without mounted disks, SQLite and ChromaDB data are wiped when containers spin down or redeploy.

---

## 🛣️ Implementation Roadmap

- [x] **Step 1: Project Setup & Health Infrastructure**
  - FastAPI modular setup with `/health` and `/ready` probes.
  - React 18 + TypeScript + Vite frontend skeleton.
  - Git hygiene, `.gitignore`, and environment configuration templates.
- [x] **Step 2: Document Ingestion & RAG Backend**
  - Multi-format parser (PyMuPDF for PDF, plus TXT and Markdown).
  - Sliding-window text chunker preserving page numbers and document provenance.
  - Persistent ChromaDB vector store beneath `data/vector_store`.
  - Sentence Transformers (`all-MiniLM-L6-v2`) dense embedding service.
  - SQLite metadata tracking with SHA-256 duplicate detection.
  - Document management API (`/upload`, list, detail, delete with cascading cleanup).
  - Semantic question-answering API (`/query`) with source citations and latency profiling.
  - Configurable LLM provider (OpenAI, Anthropic, Fake) with actionable error on missing configuration.
  - Prompt injection mitigation and evidence-based abstention.
- [x] **Step 3: Frontend Integration & Interactive UI**
  - Drag-and-drop document upload with format & size validation.
  - Document library with metadata inspection, chunk counts, and deletion with confirmation.
  - Chat-style question-answering interface displaying answers, citations, and retrieved passages.
  - Clean distinction between grounded answers and insufficient-evidence abstentions.
  - 14 Vitest frontend unit and integration tests.
- [x] **Step 4: RAG Evaluation Framework & Benchmark Suite**
  - Reproducible synthetic corpus (PDF, Markdown, TXT) and 10 curated benchmark QA pairs.
  - Deterministic evaluation metrics: Mean Recall@k, Mean Reciprocal Rank (MRR), Abstention Accuracy.
  - Answer grounding, citation provenance, and prompt injection safety tests.
  - Command-line evaluation runner (`scripts/evaluate.py`) with formatted terminal tables and machine-readable JSON reports.
- [x] **Step 5: Production Hardening & Deployment Preparation** *(Current)*
  - Non-root production `Dockerfile` with dynamic platform `$PORT` binding and `/ready` health check.
  - `.dockerignore` preventing secrets, local data, and evaluation outputs from build context.
  - Full Render Blueprint specification (`render.yaml`) with persistent disk configuration.
  - Production CORS strict validation preventing wildcard origins and empty configurations.
  - Frontend `VITE_API_BASE_URL` resolution with fallback to local proxy.
  - Safe error payload truncation preventing secret leakage from upstream providers.
  - 45 passing backend tests (health, parser, chunker, vector store, documents, query, evaluation, config).
  - 14 passing frontend tests and clean TypeScript production build.
