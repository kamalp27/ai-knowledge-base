import { useState, useEffect, useCallback } from 'react';
import { HealthStatus } from './components/HealthStatus';
import { DocumentUpload } from './components/DocumentUpload';
import { DocumentLibrary } from './components/DocumentLibrary';
import { QuestionAnswering } from './components/QuestionAnswering';
import { fetchDocuments, fetchHealth, fetchReadiness } from './services/api';
import { ApiStatusState, DocumentMetadata } from './types';
import './App.css';

export function App() {
  // System Health state
  const [statusState, setStatusState] = useState<ApiStatusState>({
    health: null,
    readiness: null,
    isLoading: true,
    error: null,
    lastChecked: null,
  });
  const [showHealthPanel, setShowHealthPanel] = useState<boolean>(false);

  // Document Library state
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(true);
  const [docsError, setDocsError] = useState<string | null>(null);

  const checkStatus = useCallback(async () => {
    setStatusState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const [health, readiness] = await Promise.all([
        fetchHealth(),
        fetchReadiness(),
      ]);
      setStatusState({
        health,
        readiness,
        isLoading: false,
        error: null,
        lastChecked: new Date().toISOString(),
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to connect to backend';
      setStatusState((prev) => ({
        ...prev,
        isLoading: false,
        error: message,
        lastChecked: new Date().toISOString(),
      }));
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setIsLoadingDocs(true);
    setDocsError(null);
    try {
      const res = await fetchDocuments();
      setDocuments(res.documents);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch document library';
      setDocsError(message);
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();
    loadDocuments();
  }, [checkStatus, loadDocuments]);

  const handleDocumentDeleted = (deletedId: string) => {
    setDocuments((prev) => prev.filter((d) => d.document_id !== deletedId));
  };

  const isHealthy = statusState.health?.status === 'ok';

  return (
    <div className="app-container">
      {/* App Header */}
      <header className="app-header">
        <div className="header-top-row">
          <div className="brand-group">
            <span className="brand-logo">🧠</span>
            <div>
              <h1 className="header-title">AI Knowledge Base</h1>
              <p className="header-subtitle">
                Document Question Answering with Retrieval-Augmented Generation (RAG)
              </p>
            </div>
          </div>

          <div className="header-controls">
            <button
              onClick={() => setShowHealthPanel(!showHealthPanel)}
              className={`system-status-pill ${isHealthy ? 'status-pill-ok' : 'status-pill-error'}`}
              title="Click to toggle system diagnostics"
            >
              <span className={`status-indicator ${isHealthy ? 'status-online' : 'status-offline'}`} />
              <span>{isHealthy ? 'Backend Operational' : 'Backend Offline'}</span>
              <span className="dropdown-caret">{showHealthPanel ? '▲' : '▼'}</span>
            </button>
            <div className="quick-links">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="link-pill"
                title="OpenAPI Swagger UI"
              >
                API Docs ↗
              </a>
            </div>
          </div>
        </div>

        {/* Collapsible Health & Diagnostics Card */}
        {showHealthPanel && (
          <div className="health-drawer">
            <HealthStatus statusState={statusState} onRefresh={checkStatus} />
          </div>
        )}
      </header>

      {/* Main Two-Column Application Layout */}
      <main className="app-main-layout">
        {/* Left Column: Ingestion & Knowledge Base Library */}
        <section className="layout-col layout-sidebar">
          <DocumentUpload onUploadSuccess={() => loadDocuments()} />
          <DocumentLibrary
            documents={documents}
            isLoading={isLoadingDocs}
            error={docsError}
            onRefresh={loadDocuments}
            onDocumentDeleted={handleDocumentDeleted}
          />
        </section>

        {/* Right Column: Semantic Chat QA & Citation Explorer */}
        <section className="layout-col layout-content">
          <QuestionAnswering documentCount={documents.length} />
        </section>
      </main>

      {/* App Footer */}
      <footer className="app-footer">
        <p>
          AI Knowledge Base • FastAPI & ChromaDB Backend • Sentence Transformers Embeddings • React 18 & TypeScript
        </p>
      </footer>
    </div>
  );
}

export default App;
