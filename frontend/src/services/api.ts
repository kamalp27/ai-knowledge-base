import {
  DocumentDeleteResponse,
  DocumentListResponse,
  DocumentMetadata,
  DocumentUploadResponse,
  HealthResponse,
  QueryRequest,
  QueryResponse,
  ReadinessResponse,
} from '../types';

// Resolve API base URL: defaults to local proxy '/api/v1'.
// If VITE_API_BASE_URL is provided (e.g. 'https://backend.onrender.com' or 'https://backend.onrender.com/api/v1'),
// ensures it points to the '/api/v1' route cleanly without duplicate slashes or repeated prefixes.
function resolveApiBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');
  if (!envUrl) {
    return '/api/v1';
  }
  return envUrl.endsWith('/api/v1') ? envUrl : `${envUrl}/api/v1`;
}

const API_BASE_URL = resolveApiBaseUrl();

export class ApiError extends Error {
  statusCode: number;
  errorType?: string;
  hint?: string;
  details?: Record<string, unknown>;

  constructor(
    message: string,
    statusCode: number,
    errorType?: string,
    hint?: string,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.errorType = errorType;
    this.hint = hint;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}: ${response.statusText}`;
    let errorType: string | undefined;
    let hint: string | undefined;
    let details: Record<string, unknown> | undefined;

    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        if (typeof errorJson.detail === 'string') {
          errorMessage = errorJson.detail;
        } else if (typeof errorJson.detail === 'object') {
          const d = errorJson.detail;
          errorMessage = d.message || d.error || JSON.stringify(d);
          errorType = d.error;
          hint = d.hint;
          details = d;
        }
      }
    } catch {
      // Body wasn't JSON, retain default status message
    }

    throw new ApiError(errorMessage, response.status, errorType, hint, details);
  }

  return response.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const url = `${API_BASE_URL}/health`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<HealthResponse>(response);
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const url = `${API_BASE_URL}/ready`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<ReadinessResponse>(response);
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const url = `${API_BASE_URL}/documents/upload`;
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    headers: {
      'Accept': 'application/json',
    },
  });

  return handleResponse<DocumentUploadResponse>(response);
}

export async function fetchDocuments(): Promise<DocumentListResponse> {
  const url = `${API_BASE_URL}/documents`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<DocumentListResponse>(response);
}

export async function fetchDocumentDetail(documentId: string): Promise<DocumentMetadata> {
  const url = `${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`;
  const response = await fetch(url, {
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<DocumentMetadata>(response);
}

export async function deleteDocument(documentId: string): Promise<DocumentDeleteResponse> {
  const url = `${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`;
  const response = await fetch(url, {
    method: 'DELETE',
    headers: { 'Accept': 'application/json' },
  });
  return handleResponse<DocumentDeleteResponse>(response);
}

export async function submitQuery(question: string, topK?: number): Promise<QueryResponse> {
  const url = `${API_BASE_URL}/query`;
  const payload: QueryRequest = {
    question: question.trim(),
    ...(topK ? { top_k: topK } : {}),
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  return handleResponse<QueryResponse>(response);
}
