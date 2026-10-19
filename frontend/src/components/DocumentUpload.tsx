import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { uploadDocument, ApiError } from '../services/api';
import { DocumentUploadResponse } from '../types';

interface DocumentUploadProps {
  onUploadSuccess: (doc: DocumentUploadResponse) => void;
}

const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md'];
const MAX_SIZE_MB = 15;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorHint, setErrorHint] = useState<string | null>(null);
  const [successResponse, setSuccessResponse] = useState<DocumentUploadResponse | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file format '${ext}'. Allowed formats: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    if (file.size === 0) {
      return 'Selected file is empty (0 bytes).';
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File exceeds maximum allowed size of ${MAX_SIZE_MB} MB (${(file.size / (1024 * 1024)).toFixed(2)} MB).`;
    }
    return null;
  };

  const handleFiles = (files: FileList | null) => {
    setErrorMessage(null);
    setErrorHint(null);
    setSuccessResponse(null);

    if (!files || files.length === 0) return;
    const file = files[0];

    const error = validateFile(file);
    if (error) {
      setErrorMessage(error);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
  };

  const handleSubmit = async () => {
    if (!selectedFile || isUploading) return;

    setIsUploading(true);
    setErrorMessage(null);
    setErrorHint(null);
    setSuccessResponse(null);

    try {
      const response = await uploadDocument(selectedFile);
      setSuccessResponse(response);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onUploadSuccess(response);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
        setErrorHint(err.hint || null);
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('An unexpected error occurred during document upload.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="card upload-card">
      <div className="card-header">
        <div className="card-title">
          <span className="overview-icon">📤</span>
          <h3>Ingest Document</h3>
        </div>
        <span className="badge-pill">PDF, TXT, MD • Max 15MB</span>
      </div>

      <div className="card-body">
        <div
          className={`dropzone ${dragActive ? 'dropzone-active' : ''} ${selectedFile ? 'dropzone-has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              fileInputRef.current?.click();
            }
          }}
          aria-label="Upload document drag and drop area"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md"
            onChange={handleChange}
            style={{ display: 'none' }}
          />

          <div className="dropzone-content">
            <span className="dropzone-icon">📄</span>
            {selectedFile ? (
              <div className="selected-file-info">
                <strong>{selectedFile.name}</strong>
                <span className="file-size-badge">{formatFileSize(selectedFile.size)}</span>
                <p className="dropzone-hint">Click or drop another file to replace</p>
              </div>
            ) : (
              <div>
                <p className="dropzone-prompt">
                  <strong>Click to select</strong> or drag and drop document here
                </p>
                <p className="dropzone-hint">Extracts text page-by-page, generates embeddings, and indexes in ChromaDB</p>
              </div>
            )}
          </div>
        </div>

        {selectedFile && (
          <div className="upload-actions">
            <button
              onClick={handleSubmit}
              disabled={isUploading}
              className="btn btn-primary"
            >
              {isUploading ? (
                <>
                  <span className="spinner" /> Indexing Document...
                </>
              ) : (
                'Upload & Index into Vector Store'
              )}
            </button>
            <button
              onClick={() => {
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
                setErrorMessage(null);
              }}
              disabled={isUploading}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        )}

        {errorMessage && (
          <div className="alert alert-error">
            <strong>Upload Failed:</strong> {errorMessage}
            {errorHint && <div className="alert-hint">{errorHint}</div>}
          </div>
        )}

        {successResponse && (
          <div className="alert alert-success">
            <strong>Success:</strong> {successResponse.message}
            <div className="success-meta">
              <span>Chunks: <strong>{successResponse.chunk_count}</strong></span>
              <span>Size: <strong>{formatFileSize(successResponse.file_size_bytes)}</strong></span>
              <span>ID: <code>{successResponse.document_id.slice(0, 8)}...</code></span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
