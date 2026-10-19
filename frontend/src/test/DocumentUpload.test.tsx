import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DocumentUpload } from '../components/DocumentUpload';
import * as api from '../services/api';

describe('DocumentUpload Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders dropzone and file input prompt', () => {
    render(<DocumentUpload onUploadSuccess={vi.fn()} />);
    expect(screen.getByText(/Click to select/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF, TXT, MD • Max 15MB/i)).toBeInTheDocument();
  });

  it('validates and rejects unsupported file formats', async () => {
    render(<DocumentUpload onUploadSuccess={vi.fn()} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const invalidFile = new File(['binary content'], 'script.exe', { type: 'application/octet-stream' });

    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(screen.getByText(/Unsupported file format '\.exe'/i)).toBeInTheDocument();
  });

  it('validates and rejects empty files', async () => {
    render(<DocumentUpload onUploadSuccess={vi.fn()} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const emptyFile = new File([], 'empty.txt', { type: 'text/plain' });

    fireEvent.change(input, { target: { files: [emptyFile] } });

    expect(screen.getByText(/Selected file is empty \(0 bytes\)/i)).toBeInTheDocument();
  });

  it('uploads valid document and triggers callback', async () => {
    const mockSuccessResponse = {
      document_id: 'doc-12345',
      filename: 'sample.pdf',
      status: 'indexed',
      chunk_count: 4,
      file_size_bytes: 2048,
      content_hash: 'abc123hash',
      message: 'Document successfully processed and indexed into knowledge base.',
    };

    vi.spyOn(api, 'uploadDocument').mockResolvedValue(mockSuccessResponse);
    const onUploadSuccess = vi.fn();

    render(<DocumentUpload onUploadSuccess={onUploadSuccess} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const validFile = new File(['PDF header text'], 'sample.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [validFile] } });

    // File info displayed
    expect(screen.getByText('sample.pdf')).toBeInTheDocument();

    const uploadBtn = screen.getByRole('button', { name: /Upload & Index into Vector Store/i });
    fireEvent.click(uploadBtn);

    await waitFor(() => {
      expect(api.uploadDocument).toHaveBeenCalledWith(validFile);
      expect(onUploadSuccess).toHaveBeenCalledWith(mockSuccessResponse);
      expect(screen.getByText(/Document successfully processed/i)).toBeInTheDocument();
    });
  });

  it('handles duplicate document API conflict error', async () => {
    const duplicateError = new api.ApiError(
      "Document 'sample.pdf' with identical content has already been indexed.",
      409,
      undefined,
      'Use existing document ID or re-upload different file.'
    );

    vi.spyOn(api, 'uploadDocument').mockRejectedValue(duplicateError);

    render(<DocumentUpload onUploadSuccess={vi.fn()} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const validFile = new File(['PDF content'], 'sample.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [validFile] } });

    const uploadBtn = screen.getByRole('button', { name: /Upload & Index into Vector Store/i });
    fireEvent.click(uploadBtn);

    await waitFor(() => {
      expect(screen.getByText(/already been indexed/i)).toBeInTheDocument();
      expect(screen.getByText(/Use existing document ID/i)).toBeInTheDocument();
    });
  });
});
