from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.config import Settings, get_settings
from backend.app.models.query import QueryRequest, QueryResponse
from backend.app.rag.dependencies import get_query_service
from backend.app.rag.llm import LLMConfigurationError
from backend.app.rag.query_service import QueryService

router = APIRouter()


@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Question Answering",
    description="Answer questions grounded solely in uploaded documents using vector similarity retrieval and LLM synthesis.",
)
async def query_knowledge_base(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
    query_service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    try:
        response = query_service.answer_query(
            request=request,
            default_top_k=settings.TOP_K,
        )
        return response
    except LLMConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "LLM_NOT_CONFIGURED",
                "message": str(e),
                "hint": "Set LLM_PROVIDER ('openai' or 'anthropic') and supply the corresponding API key in your .env file, or set LLM_PROVIDER=fake for testing.",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering your question: {str(e)}",
        )
