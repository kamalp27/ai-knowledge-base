import time
from typing import List, Optional
from backend.app.models.query import (
    Citation,
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
    TimingInfo,
)
from backend.app.rag.llm import BaseLLMProvider
from backend.app.rag.retrieval import RetrievalService


class QueryService:
    """Orchestrates question answering over retrieved document context."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_provider: BaseLLMProvider,
    ):
        self.retrieval_service = retrieval_service
        self.llm_provider = llm_provider

    def answer_query(self, request: QueryRequest, default_top_k: int = 4) -> QueryResponse:
        start_time = time.perf_counter()
        top_k = request.top_k if request.top_k is not None else default_top_k

        # 1. Retrieval Phase
        retrieval_start = time.perf_counter()
        retrieved_chunks: List[RetrievedChunk] = self.retrieval_service.retrieve(
            query=request.question,
            top_k=top_k,
        )
        retrieval_time_ms = round((time.perf_counter() - retrieval_start) * 1000, 2)

        # 2. Check for insufficient evidence
        if not retrieved_chunks:
            total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return QueryResponse(
                question=request.question,
                answer="I could not find sufficient evidence in the uploaded documents to answer your question.",
                citations=[],
                retrieved_chunks=[],
                timing=TimingInfo(
                    retrieval_time_ms=retrieval_time_ms,
                    llm_time_ms=0.0,
                    total_time_ms=total_time_ms,
                ),
                evidence_found=False,
            )

        # 3. Format grounded context with untrusted-input delimiters
        context_blocks = []
        citations: List[Citation] = []

        for idx, chunk in enumerate(retrieved_chunks):
            page_str = f"Page {chunk.page_number}" if chunk.page_number else "Page N/A"
            header = f"[Source {idx + 1}: {chunk.filename} ({page_str})]"
            # Sanitize any attempted delimiter breakouts
            clean_text = chunk.text.replace("--- CONTEXT END ---", "[FILTERED]")
            context_blocks.append(f"{header}\n{clean_text}")

            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    chunk_id=chunk.chunk_id,
                    snippet=chunk.text[:200] + ("..." if len(chunk.text) > 200 else ""),
                )
            )

        grounded_context = "\n\n".join(context_blocks)

        # 4. LLM Generation Phase
        llm_start = time.perf_counter()
        answer = self.llm_provider.generate_answer(
            question=request.question,
            context=grounded_context,
        )
        llm_time_ms = round((time.perf_counter() - llm_start) * 1000, 2)
        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 5. Check if answer is an abstention
        answer_lower = answer.lower()
        is_abstention = (
            "could not find sufficient evidence" in answer_lower
            or "insufficient evidence" in answer_lower
            or "not enough information" in answer_lower
        )
        evidence_found = not is_abstention

        return QueryResponse(
            question=request.question,
            answer=answer,
            citations=citations,
            retrieved_chunks=retrieved_chunks,
            timing=TimingInfo(
                retrieval_time_ms=retrieval_time_ms,
                llm_time_ms=llm_time_ms,
                total_time_ms=total_time_ms,
            ),
            evidence_found=evidence_found,
        )
