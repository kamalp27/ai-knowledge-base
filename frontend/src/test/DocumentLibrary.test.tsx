import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DocumentLibrary } from '../components/DocumentLibrary';
import * as api from '../services/api';
import { DocumentMetadata } from '../types';

const mockDocs: DocumentMetadata[] = [
  {
    document_id: 'doc-aaa-111',
    filename: 'architecture.pdf',
    file_size_bytes: 10240,
    content_hash: 'hash-aaa',
    chunk_count: 5,
    created_at: '2026-10-20T00:00:00Z',
    status: 'indexed',
  },
  {
    document_id: 'doc-bbb-222',
    filename: 'notes.md',
    file_size_bytes: 512,
    content_hash: 'hash-bbb',
    chunk_count: 2,
    created_at: '2026-10-20T01:00:00Z',
    status: 'indexed',
  },
];

describe('DocumentLibrary Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders list of indexed documents', () => {
    render(
      <DocumentLibrary
        documents={mockDocs}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        onDocumentDeleted={vi.fn()}
      />
    );

    expect(screen.getByText('architecture.pdf')).toBeInTheDocument();
    expect(screen.getByText('notes.md')).toBeInTheDocument();
    expect(screen.getByText('5 chunks')).toBeInTheDocument();
    expect(screen.getByText('2 chunks')).toBeInTheDocument();
  });

  it('renders empty state when no documents exist', () => {
    render(
      <DocumentLibrary
        documents={[]}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        onDocumentDeleted={vi.fn()}
      />
    );

    expect(screen.getByText(/No Documents Indexed/i)).toBeInTheDocument();
  });

  it('renders loading state', () => {
    render(
      <DocumentLibrary
        documents={[]}
        isLoading={true}
        error={null}
        onRefresh={vi.fn()}
        onDocumentDeleted={vi.fn()}
      />
    );

    expect(screen.getByText(/Loading indexed knowledge base documents/i)).toBeInTheDocument();
  });

  it('opens detail modal on inspect click', async () => {
    vi.spyOn(api, 'fetchDocumentDetail').mockResolvedValue(mockDocs[0]);

    render(
      <DocumentLibrary
        documents={mockDocs}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        onDocumentDeleted={vi.fn()}
      />
    );

    const inspectButtons = screen.getAllByTitle('View details');
    fireEvent.click(inspectButtons[0]);

    await waitFor(() => {
      expect(api.fetchDocumentDetail).toHaveBeenCalledWith('doc-aaa-111');
      expect(screen.getByText('Document Details')).toBeInTheDocument();
      expect(screen.getByText('hash-aaa')).toBeInTheDocument();
    });
  });

  it('shows confirmation and executes document deletion', async () => {
    vi.spyOn(api, 'deleteDocument').mockResolvedValue({
      document_id: 'doc-aaa-111',
      deleted: true,
      message: 'Deleted successfully',
    });

    const onDeleted = vi.fn();

    render(
      <DocumentLibrary
        documents={mockDocs}
        isLoading={false}
        error={null}
        onRefresh={vi.fn()}
        onDocumentDeleted={onDeleted}
      />
    );

    const deleteButtons = screen.getAllByTitle('Delete document');
    fireEvent.click(deleteButtons[0]);

    // Confirmation dialog appears
    expect(screen.getByText(/Confirm Document Deletion/i)).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to permanently delete/i)).toBeInTheDocument();

    const confirmBtn = screen.getByRole('button', { name: /Delete Permanently/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(api.deleteDocument).toHaveBeenCalledWith('doc-aaa-111');
      expect(onDeleted).toHaveBeenCalledWith('doc-aaa-111');
    });
  });
});
