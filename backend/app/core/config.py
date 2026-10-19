from functools import lru_cache
import json
from typing import Any, List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings loaded from environment or .env file."""

    APP_NAME: str = "AI Knowledge Base"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    PORT: Optional[int] = None  # Cloud platform dynamic port support ($PORT)
    DEBUG: bool = True
    VERSION: str = "0.2.0"
    API_V1_PREFIX: str = "/api/v1"

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Support JSON arrays, comma-delimited strings, or native lists for CORS_ORIGINS."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(item).strip() for item in v]
        return v

    @model_validator(mode="after")
    def validate_production_and_port(self) -> "Settings":
        """Enforce production security rules and sync platform PORT."""
        if self.PORT is not None:
            self.APP_PORT = self.PORT

        # Production security check: disallow wildcard '*' or empty origins in production
        if self.APP_ENV.lower() == "production":
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Wildcard '*' in CORS_ORIGINS is prohibited in production mode. "
                    "Configure explicit frontend origins (e.g. https://my-frontend.onrender.com)."
                )
            if not self.CORS_ORIGINS:
                raise ValueError(
                    "CORS_ORIGINS cannot be empty in production mode. "
                    "Configure at least one allowed frontend origin."
                )

        return self

    # File Upload Limits & Formats
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".md"]

    # Storage paths
    DATA_DIR: str = "./data"
    RAW_DOCUMENTS_DIR: str = "./data/raw_documents"
    VECTOR_STORE_DIR: str = "./data/vector_store"
    EVAL_DATASETS_DIR: str = "./data/eval_datasets"
    METADATA_DB_PATH: str = "./data/metadata.db"

    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Embeddings Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHROMA_COLLECTION_NAME: str = "knowledge_base"

    # Retrieval Configuration
    TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.0

    # LLM Provider Configuration
    LLM_PROVIDER: str = "none"  # "none", "fake", "openai", "anthropic"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_API_BASE: str = "https://api.anthropic.com/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
