import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { submitQuery, ApiError } from '../services/api';
import { ChatMessage, Citation, RetrievedChunk } from '../types';

interface QuestionAnsweringProps {
  documentCount: number;
}

export const QuestionAnswering: React.FC<QuestionAnsweringProps> = ({ documentCount }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuestion, setInputQuestion] = useState<string>('');
  const [topK, setTopK] = useState<number>(4);
  const [isQuerying, setIsQuerying] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(false);
  const [activeTabByMsgId, setActiveTabByMsgId] = useState<Record<string, 'answer' | 'citations' | 'chunks'>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleTabChange = (msgId: string, tab: 'answer' | 'citations' | 'chunks') => {
    setActiveTabByMsgId((prev) => ({ ...prev, [msgId]: tab }));
  };

  const handleSend = async () => {
    const trimmed = inputQuestion.trim();
    if (!trimmed || isQuerying) return;

    const messageId = `msg_${Date.now()}`;
    const newMsg: ChatMessage = {
      id: messageId,
      question: trimmed,
      timestamp: new Date().toISOString(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, newMsg]);
    setInputQuestion('');
    setIsQuerying(true);

    try {
      const response = await submitQuery(trimmed, topK);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, response, isLoading: false }
            : msg
        )
      );
    } catch (err: unknown) {
      let errMsg = 'Failed to answer question.';
      let errHint: string | undefined;

      if (err instanceof ApiError) {
        errMsg = err.message;
        errHint = err.hint;
      } else if (err instanceof Error) {
        errMsg = err.message;
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, error: errMsg, errorHint: errHint, isLoading: false }
            : msg
        )
      );
    } finally {
      setIsQuerying(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setActiveTabByMsgId({});
  };

  return (
    <div className="card chat-card">
      <div className="card-header">
        <div className="card-title">
          <span className="overview-icon">💬</span>
          <h3>Document Question Answering</h3>
        </div>
        <div className="chat-header-actions">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="btn btn-secondary btn-sm"
            title="Configure retrieval top-k"
          >
            ⚙️ Settings {showConfig ? '▲' : '▼'}
          </button>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              disabled={isQuerying}
              className="btn btn-secondary btn-sm"
              title="Clear current session chat history"
            >
              Clear Session
            </button>
          )}
        </div>
      </div>

      {showConfig && (
        <div className="config-banner">
          <label htmlFor="top-k-input">
            Top-K Passages to Retrieve: <strong>{topK}</strong>
          </label>
          <input
            id="top-k-input"
            type="range"
            min="1"
            max="10"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value, 10))}
            className="slider"
          />
          <span className="config-hint">Retrieves top {topK} semantic context chunks from ChromaDB</span>
        </div>
      )}

      <div className="card-body chat-body">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="welcome-icon">🔍</div>
            <h4>Ask Questions Across Your Indexed Documents</h4>
            <p>
              Submit a natural language question. The system will retrieve relevant chunks via vector similarity, inject grounded context into the prompt, and return factual answers with source citations.
            </p>
            {documentCount === 0 && (
              <div className="alert alert-warning">
                <strong>Notice:</strong> No documents have been indexed yet. Upload documents in the library to enable evidence retrieval.
              </div>
            )}
            <div className="sample-prompts">
              <span className="sample-label">Try asking:</span>
              <button
                className="prompt-chip"
                onClick={() => setInputQuestion('What is the main topic of the uploaded document?')}
              >
                "What is the main topic of the uploaded document?"
              </button>
              <button
                className="prompt-chip"
                onClick={() => setInputQuestion('Summarize the key architectural components.')}
              >
                "Summarize the key architectural components."
              </button>
            </div>
          </div>
        ) : (
          <div className="messages-stream">
            {messages.map((msg) => {
              const activeTab = activeTabByMsgId[msg.id] || 'answer';
              const resp = msg.response;

              return (
                <div key={msg.id} className="message-block">
                  {/* User Question */}
                  <div className="message-user">
                    <div className="msg-header">
                      <span className="avatar avatar-user">You</span>
                      <span className="msg-time">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <div className="user-query-text">{msg.question}</div>
                  </div>

                  {/* Assistant Response */}
                  <div className="message-assistant">
                    <div className="msg-header">
                      <span className="avatar avatar-bot">AI Assistant</span>
                      {resp && (
                        <div className="status-badges-group">
                          {resp.evidence_found ? (
                            <span className="badge-evidence badge-grounded">
                              ✓ Grounded with Evidence
                            </span>
                          ) : (
                            <span className="badge-evidence badge-abstained">
                              ⚠ Insufficient Evidence (Abstained)
                            </span>
                          )}
                          <span className="timing-pill" title="Execution latency">
                            ⚡ {resp.timing.total_time_ms} ms (retrieval: {resp.timing.retrieval_time_ms}ms, llm: {resp.timing.llm_time_ms}ms)
                          </span>
                        </div>
                      )}
                    </div>

                    {msg.isLoading ? (
                      <div className="loading-state">
                        <span className="spinner" />
                        <span>Searching vector index & synthesizing grounded response...</span>
                      </div>
                    ) : msg.error ? (
                      <div className="alert alert-error">
                        <strong>Query Failed:</strong> {msg.error}
                        {msg.errorHint && (
                          <div className="alert-hint">
                            <strong>Setup hint:</strong> {msg.errorHint}
                          </div>
                        )}
                      </div>
                    ) : resp ? (
                      <div className="response-content">
                        {/* Tab Navigation if citations/chunks exist */}
                        {resp.citations.length > 0 && (
                          <div className="response-tabs">
                            <button
                              className={`tab-btn ${activeTab === 'answer' ? 'tab-active' : ''}`}
                              onClick={() => handleTabChange(msg.id, 'answer')}
                            >
                              Grounded Answer
                            </button>
                            <button
                              className={`tab-btn ${activeTab === 'citations' ? 'tab-active' : ''}`}
                              onClick={() => handleTabChange(msg.id, 'citations')}
                            >
                              Citations ({resp.citations.length})
                            </button>
                            <button
                              className={`tab-btn ${activeTab === 'chunks' ? 'tab-active' : ''}`}
                              onClick={() => handleTabChange(msg.id, 'chunks')}
                            >
                              Retrieved Passages ({resp.retrieved_chunks.length})
                            </button>
                          </div>
                        )}

                        {/* Tab 1: Answer */}
                        {activeTab === 'answer' && (
                          <div className="answer-text">
                            {resp.answer}
                          </div>
                        )}

                        {/* Tab 2: Citations */}
                        {activeTab === 'citations' && (
                          <div className="citations-list">
                            {resp.citations.map((c: Citation, idx: number) => (
                              <div key={idx} className="citation-card">
                                <div className="citation-header">
                                  <span className="citation-num">#{idx + 1}</span>
                                  <strong>{c.filename}</strong>
                                  {c.page_number && <span className="citation-page">Page {c.page_number}</span>}
                                  <code className="citation-chunk-id">{c.chunk_id}</code>
                                </div>
                                <div className="citation-snippet">"{c.snippet}"</div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Tab 3: Retrieved Chunks */}
                        {activeTab === 'chunks' && (
                          <div className="chunks-list">
                            {resp.retrieved_chunks.map((chunk: RetrievedChunk, idx: number) => (
                              <div key={idx} className="chunk-card">
                                <div className="chunk-header">
                                  <span className="chunk-rank">Passage {idx + 1}</span>
                                  <span className="chunk-source">{chunk.filename} {chunk.page_number ? `(p. ${chunk.page_number})` : ''}</span>
                                  <span className="similarity-badge">
                                    Similarity: {(chunk.score * 100).toFixed(1)}%
                                  </span>
                                </div>
                                <pre className="chunk-raw-text">{chunk.text}</pre>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="chat-input-bar">
        <textarea
          ref={textareaRef}
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your uploaded documents... (Press Enter to submit, Shift+Enter for newline)"
          rows={2}
          disabled={isQuerying}
          className="chat-textarea"
          aria-label="Ask a question about your documents"
        />
        <button
          onClick={handleSend}
          disabled={isQuerying || !inputQuestion.trim()}
          className="btn btn-primary send-btn"
          title="Submit question"
        >
          {isQuerying ? <span className="spinner" /> : 'Send ↵'}
        </button>
      </div>
    </div>
  );
};
