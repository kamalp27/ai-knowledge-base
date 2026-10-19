export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface ReadinessResponse {
  status: string;
  storage_ready: boolean;
  services: Record<string, string>;
  timestamp: string;
}

export interface ApiStatusState {
  health: HealthResponse | null;
  readiness: ReadinessResponse | null;
  isLoading: boolean;
  error: string | null;
  lastChecked: string | null;
}

export interface DocumentMetadata {
  document_id: string;
  filename: string;
  file_size_bytes: number;
  content_hash: string;
  chunk_count: number;
  created_at: string;
  status: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: string;
  chunk_count: number;
  file_size_bytes: number;
  content_hash: string;
  message: string;
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentMetadata[];
}

export interface DocumentDeleteResponse {
  document_id: string;
  deleted: boolean;
  message: string;
}

export interface Citation {
  document_id: string;
  filename: string;
  page_number?: number | null;
  chunk_id: string;
  snippet: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number?: number | null;
  text: string;
  score: number;
}

export interface TimingInfo {
  retrieval_time_ms: number;
  llm_time_ms: number;
  total_time_ms: number;
}

export interface QueryRequest {
  question: string;
  top_k?: number;
}

export interface QueryResponse {
  question: string;
  answer: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunk[];
  timing: TimingInfo;
  evidence_found: boolean;
}

export interface ChatMessage {
  id: string;
  question: string;
  response?: QueryResponse;
  error?: string;
  errorHint?: string;
  timestamp: string;
  isLoading?: boolean;
}
