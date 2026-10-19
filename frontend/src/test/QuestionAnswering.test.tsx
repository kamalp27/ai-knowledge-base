import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QuestionAnswering } from '../components/QuestionAnswering';
import * as api from '../services/api';
import { QueryResponse } from '../types';

describe('QuestionAnswering Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders welcome screen when chat is empty', () => {
    render(<QuestionAnswering documentCount={2} />);
    expect(screen.getByText(/Ask Questions Across Your Indexed Documents/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask a question about your uploaded documents/i)).toBeInTheDocument();
  });

  it('submits query and renders grounded answer with citations and timing', async () => {
    const mockQueryResponse: QueryResponse = {
      question: 'What is ChromaDB?',
      answer: 'ChromaDB is an open-source vector database built for AI applications.',
      citations: [
        {
          document_id: 'doc-1',
          filename: 'chroma_guide.pdf',
          page_number: 3,
          chunk_id: 'doc-1_c2',
          snippet: 'Chroma is an open-source vector database designed for AI embeddings.',
        },
      ],
      retrieved_chunks: [
        {
          chunk_id: 'doc-1_c2',
          document_id: 'doc-1',
          filename: 'chroma_guide.pdf',
          page_number: 3,
          text: 'Full passage text from chroma_guide page 3.',
          score: 0.942,
        },
      ],
      timing: {
        retrieval_time_ms: 12.5,
        llm_time_ms: 240.0,
        total_time_ms: 252.5,
      },
      evidence_found: true,
    };

    vi.spyOn(api, 'submitQuery').mockResolvedValue(mockQueryResponse);

    render(<QuestionAnswering documentCount={1} />);

    const textarea = screen.getByPlaceholderText(/Ask a question about your uploaded documents/i);
    fireEvent.change(textarea, { target: { value: 'What is ChromaDB?' } });

    const sendBtn = screen.getByRole('button', { name: /Send ↵/i });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(api.submitQuery).toHaveBeenCalledWith('What is ChromaDB?', 4);
      expect(screen.getByText('ChromaDB is an open-source vector database built for AI applications.')).toBeInTheDocument();
      expect(screen.getByText(/✓ Grounded with Evidence/i)).toBeInTheDocument();
      expect(screen.getByText(/252.5 ms/i)).toBeInTheDocument();
    });

    // Citations tab
    const citationsTab = screen.getByRole('button', { name: /Citations \(1\)/i });
    fireEvent.click(citationsTab);

    expect(screen.getByText('chroma_guide.pdf')).toBeInTheDocument();
    expect(screen.getByText('Page 3')).toBeInTheDocument();
    expect(screen.getByText(/"Chroma is an open-source vector database designed for AI embeddings\."/i)).toBeInTheDocument();
  });

  it('renders abstention badge when evidence is insufficient', async () => {
    const mockAbstention: QueryResponse = {
      question: 'What is the speed of light on Neptune?',
      answer: 'I could not find sufficient evidence in the uploaded documents to answer your question.',
      citations: [],
      retrieved_chunks: [],
      timing: {
        retrieval_time_ms: 8.0,
        llm_time_ms: 0.0,
        total_time_ms: 8.0,
      },
      evidence_found: false,
    };

    vi.spyOn(api, 'submitQuery').mockResolvedValue(mockAbstention);

    render(<QuestionAnswering documentCount={1} />);

    const textarea = screen.getByPlaceholderText(/Ask a question about your uploaded documents/i);
    fireEvent.change(textarea, { target: { value: 'What is the speed of light on Neptune?' } });

    const sendBtn = screen.getByRole('button', { name: /Send ↵/i });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/⚠ Insufficient Evidence \(Abstained\)/i)).toBeInTheDocument();
      expect(screen.getByText(/I could not find sufficient evidence in the uploaded documents/i)).toBeInTheDocument();
    });
  });

  it('displays LLM configuration error with setup hint', async () => {
    const llmError = new api.ApiError(
      'No LLM provider configured.',
      503,
      'LLM_NOT_CONFIGURED',
      'Set LLM_PROVIDER=openai and OPENAI_API_KEY in .env file.'
    );

    vi.spyOn(api, 'submitQuery').mockRejectedValue(llmError);

    render(<QuestionAnswering documentCount={1} />);

    const textarea = screen.getByPlaceholderText(/Ask a question about your uploaded documents/i);
    fireEvent.change(textarea, { target: { value: 'Tell me about the documents' } });

    const sendBtn = screen.getByRole('button', { name: /Send ↵/i });
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/No LLM provider configured\./i)).toBeInTheDocument();
      expect(screen.getByText(/Set LLM_PROVIDER=openai/i)).toBeInTheDocument();
    });
  });
});
