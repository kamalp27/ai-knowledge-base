# Architecture & Deployment Guide — AI Knowledge Base

## 1. System Topology & Component Architecture

```text
+-------------------------------------------------------------------------------+
|                           CLIENT LAYER (Browser)                             |
|                                                                               |
|  React 18 + TypeScript + Vite SPA                                             |
|  - Drag & Drop Document Ingestion UI                                          |
|  - Document Library Management (SHA-256 duplicate detection)                 |
|  - Grounded Question-Answering Chat Interface (Citations & Timing)           |
+-------------------------------------------------------------------------------+
                                    │
                                    │ HTTPS / REST (Configurable via VITE_API_BASE_URL)
                                    ▼
+-------------------------------------------------------------------------------+
|                       API & APPLICATION LAYER (FastAPI)                       |
|                                                                               |
|  FastAPI ASGI Application (Bound to 0.0.0.0:${PORT})                          |
|  - CORS Security Policy (Restricts origins strictly to configured frontends)  |
|  - Liveness & Readiness Probes (/health, /ready)                             |
|  - Router (/api/v1): /documents, /query, /health, /ready                     |
+-------------------------------------------------------------------------------+
           │                                                │
           ▼                                                ▼
+---------------------------------------+    +----------------------------------+
|           RAG RETRIEVAL ENGINE         |    |         LLM SYNTHESIS LAYER      |
|                                       |    |                                  |
| - PyMuPDF Extractor (PDF, TXT, MD)    |    | - Grounded Prompt Builder        |
| - Provenance-Preserving Chunker       |    | - Delimiter Breakout Sanitizer   |
| - Dense SentenceTransformers          |    | - Providers:                     |
|   (all-MiniLM-L6-v2)                  |    |   • OpenAI (gpt-4o-mini)         |
|                                       |    |   • Anthropic (claude-3-5)       |
|                                       |    |   • Fake (deterministic tests)   |
+---------------------------------------+    +----------------------------------+
           │                    │                           │
           ▼                    ▼                           ▼
+--------------------+ +--------------------+    +-----------------------------+
|  METADATA STORE    | |   VECTOR DATABASE   |    |      EVALUATION ENGINE      |
|                    | |                    |    |                             |
| SQLite Repository  | | Persistent ChromaDB|    | RAGEvaluationRunner         |
| (Files, Hashes,    | | Collections & Dense|    | - Recall@k                  |
|  Page Provenance)  | | Embeddings Cache   |    | - Mean Reciprocal Rank (MRR)|
+--------------------+ +--------------------+    | - Abstention Accuracy       |
           │                    │                +-----------------------------+
           └────────────────────┼───────────────────────────────┘
                                ▼
         +---------------------------------------------+
         |           PERSISTENT STORAGE VOLUME         |
         |                                             |
         | Mounted Disk (/app/data):                   |
         | ├── raw_documents/                          |
         | ├── vector_store/                           |
         | └── metadata.db                             |
         +---------------------------------------------+
```

---

## 2. Production Hosting & Persistence Model

### Deployment Pattern: Containerized Web Service + Static Site
- **Backend Service**: Packaged via Docker (`Dockerfile`) on `python:3.12-slim` running as an unprivileged user (`appuser`). The container binds to `0.0.0.0` and listens on the host-assigned `$PORT`.
- **Frontend Static Site**: Static assets compiled via `npm run build` (`vite build`) and deployed to a global CDN (e.g., Render Static Sites, Vercel, Netlify, or Cloudflare Pages).
- **Persistent Disk**: Mounted at `/app/data` to ensure SQLite database records, uploaded raw documents, and ChromaDB vector indices persist across restarts, redeployments, and image rebuilds.

### Storage Constraints & Scalability
> [!IMPORTANT]
> **Single Instance Disk Constraint**:
> Embedded ChromaDB and SQLite operate on a local disk filesystem. They do not support concurrent multi-container write access across distributed nodes.
> - On platforms like Render, the backend service must run as **1 replica** with a persistent disk attached.
> - For horizontal multi-instance scaling in future enterprise tiers, the vector store can be transitioned to a standalone vector service (e.g., Qdrant, Pinecone, or Chroma Server) and the metadata repository to PostgreSQL.

---

## 3. Security & Hardening Architecture

1. **Origin Restraint (CORS)**:
   - In production (`APP_ENV=production`), wildcard origins (`*`) and empty origin lists are strictly rejected at startup via Pydantic validators.
   - Frontends must be explicitly configured via `CORS_ORIGINS` (supporting comma-separated lists or JSON arrays).

2. **Zero Client Secrets**:
   - The browser frontend only receives `VITE_API_BASE_URL`.
   - LLM API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) and database credentials are kept exclusively in server-side runtime memory.

3. **Adversarial Prompt Injection Defense**:
   - Document contexts injected into prompts are isolated inside untrusted content delimiters (`--- UNTRUSTED CONTEXT START ---`).
   - Any attempt by user documents to break out of delimiters (`--- CONTEXT END ---`) is sanitized before being passed to LLM generation.
   - Fake and real LLM providers evaluate context factuality before responding, abstaining if evidence is insufficient or malicious instructions are detected.

4. **Resource Exhaustion & Upload Limits**:
   - Upload streams are consumed in 64 KB chunks and bounded by `MAX_UPLOAD_SIZE_MB` (15 MB default). Exceeding this limit terminates the upload stream with HTTP 413, preventing memory exhaustion.
