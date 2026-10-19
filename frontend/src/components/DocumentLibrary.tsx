import React, { useState } from 'react';
import { DocumentMetadata } from '../types';
import { deleteDocument, fetchDocumentDetail, ApiError } from '../services/api';

interface DocumentLibraryProps {
  documents: DocumentMetadata[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  onDocumentDeleted: (documentId: string) => void;
}

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({
  documents,
  isLoading,
  error,
  onRefresh,
  onDocumentDeleted,
}) => {
  const [selectedDoc, setSelectedDoc] = useState<DocumentMetadata | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [documentToDelete, setDocumentToDelete] = useState<DocumentMetadata | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleInspect = async (docId: string) => {
    setIsDetailLoading(true);
    setDetailError(null);
    try {
      const detail = await fetchDocumentDetail(docId);
      setSelectedDoc(detail);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load document details.';
      setDetailError(msg);
    } finally {
      setIsDetailLoading(false);
    }
  };

  const confirmDelete = async () => {
    if (!documentToDelete || isDeleting) return;

    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteDocument(documentToDelete.document_id);
      onDocumentDeleted(documentToDelete.document_id);
      setDocumentToDelete(null);
      if (selectedDoc?.document_id === documentToDelete.document_id) {
        setSelectedDoc(null);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setDeleteError(err.message);
      } else if (err instanceof Error) {
        setDeleteError(err.message);
      } else {
        setDeleteError('Failed to delete document.');
      }
    } finally {
      setIsDeleting(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (isoString: string): string => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="card library-card">
      <div className="card-header">
        <div className="card-title">
          <span className="overview-icon">📚</span>
          <h3>Document Library</h3>
          <span className="badge-counter">{documents.length}</span>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="btn btn-secondary btn-sm"
          title="Refresh library"
        >
          {isLoading ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>

      <div className="card-body">
        {error && (
          <div className="alert alert-error">
            <strong>Error loading library:</strong> {error}
          </div>
        )}

        {isLoading && documents.length === 0 ? (
          <div className="empty-state">
            <span className="spinner" />
            <p>Loading indexed knowledge base documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">📂</span>
            <h4>No Documents Indexed</h4>
            <p>Upload your first PDF, TXT, or Markdown document above to enable semantic question answering.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="documents-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Chunks</th>
                  <th>Size</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.document_id}>
                    <td className="doc-name-cell">
                      <span className="doc-icon">
                        {doc.filename.endsWith('.pdf') ? '📕' : doc.filename.endsWith('.md') ? '📘' : '📄'}
                      </span>
                      <div className="doc-name-wrapper">
                        <span className="doc-filename" title={doc.filename}>{doc.filename}</span>
                        <code className="doc-id-sub">{doc.document_id.slice(0, 8)}...</code>
                      </div>
                    </td>
                    <td>
                      <span className="badge-pill chunk-pill">{doc.chunk_count} chunks</span>
                    </td>
                    <td className="text-muted-cell">{formatFileSize(doc.file_size_bytes)}</td>
                    <td>
                      <span className={`status-badge ${doc.status === 'indexed' ? 'badge-success' : 'badge-warning'}`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="doc-actions-cell">
                      <button
                        onClick={() => handleInspect(doc.document_id)}
                        className="btn-icon"
                        title="View details"
                      >
                        🔍
                      </button>
                      <button
                        onClick={() => setDocumentToDelete(doc)}
                        className="btn-icon btn-icon-danger"
                        title="Delete document"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Document Detail Modal */}
        {selectedDoc && (
          <div className="modal-backdrop" onClick={() => setSelectedDoc(null)}>
            <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Document Details</h3>
                <button className="modal-close" onClick={() => setSelectedDoc(null)}>×</button>
              </div>
              <div className="modal-body">
                {isDetailLoading ? (
                  <div className="modal-loading"><span className="spinner" /> Loading details...</div>
                ) : detailError ? (
                  <div className="alert alert-error">{detailError}</div>
                ) : (
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>Filename</label>
                      <div className="detail-val"><strong>{selectedDoc.filename}</strong></div>
                    </div>
                    <div className="detail-item">
                      <label>Document ID</label>
                      <div className="detail-val"><code>{selectedDoc.document_id}</code></div>
                    </div>
                    <div className="detail-item">
                      <label>Indexed Chunks</label>
                      <div className="detail-val">{selectedDoc.chunk_count} chunks stored in ChromaDB</div>
                    </div>
                    <div className="detail-item">
                      <label>File Size</label>
                      <div className="detail-val">{formatFileSize(selectedDoc.file_size_bytes)} ({selectedDoc.file_size_bytes} bytes)</div>
                    </div>
                    <div className="detail-item">
                      <label>Ingestion Date</label>
                      <div className="detail-val">{formatDate(selectedDoc.created_at)}</div>
                    </div>
                    <div className="detail-item full-width">
                      <label>SHA-256 Content Hash</label>
                      <div className="detail-val"><code className="hash-code">{selectedDoc.content_hash}</code></div>
                    </div>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setSelectedDoc(null)}>Close</button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {documentToDelete && (
          <div className="modal-backdrop" onClick={() => !isDeleting && setDocumentToDelete(null)}>
            <div className="modal-dialog modal-danger" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Confirm Document Deletion</h3>
                <button
                  className="modal-close"
                  onClick={() => !isDeleting && setDocumentToDelete(null)}
                  disabled={isDeleting}
                >
                  ×
                </button>
              </div>
              <div className="modal-body">
                <p>
                  Are you sure you want to permanently delete <strong>{documentToDelete.filename}</strong>?
                </p>
                <p className="danger-text">
                  This will remove the raw file, its SQLite metadata record, and all <strong>{documentToDelete.chunk_count}</strong> vector embeddings from ChromaDB.
                </p>

                {deleteError && (
                  <div className="alert alert-error">
                    {deleteError}
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={() => setDocumentToDelete(null)}
                  disabled={isDeleting}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-danger"
                  onClick={confirmDelete}
                  disabled={isDeleting}
                >
                  {isDeleting ? 'Deleting...' : 'Delete Permanently'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
