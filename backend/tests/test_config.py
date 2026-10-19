import pytest
from pydantic import ValidationError
from backend.app.core.config import Settings


def test_cors_origins_parsing_comma_separated():
    """Verify that comma-separated CORS_ORIGINS string is parsed into list."""
    settings = Settings(
        CORS_ORIGINS="https://example.com, https://app.example.com",
        APP_ENV="development",
    )
    assert settings.CORS_ORIGINS == ["https://example.com", "https://app.example.com"]


def test_cors_origins_parsing_json_string():
    """Verify that JSON-encoded CORS_ORIGINS string is parsed into list."""
    settings = Settings(
        CORS_ORIGINS='["https://frontend.onrender.com", "http://localhost:5173"]',
        APP_ENV="development",
    )
    assert settings.CORS_ORIGINS == ["https://frontend.onrender.com", "http://localhost:5173"]


def test_cors_origins_native_list():
    """Verify that native Python list remains intact."""
    settings = Settings(
        CORS_ORIGINS=["https://frontend.onrender.com"],
        APP_ENV="development",
    )
    assert settings.CORS_ORIGINS == ["https://frontend.onrender.com"]


def test_port_environment_override():
    """Verify that cloud hosting platform PORT variable overrides APP_PORT."""
    settings = Settings(PORT=10000, APP_ENV="development")
    assert settings.APP_PORT == 10000


def test_production_wildcard_cors_rejected():
    """Verify that wildcard '*' CORS is strictly prohibited in production mode."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_ENV="production",
            CORS_ORIGINS=["*"],
        )
    assert "Wildcard '*' in CORS_ORIGINS is prohibited in production mode" in str(exc_info.value)


def test_production_empty_cors_rejected():
    """Verify that empty CORS origins list is rejected in production mode."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_ENV="production",
            CORS_ORIGINS="",
        )
    assert "CORS_ORIGINS cannot be empty in production mode" in str(exc_info.value)


def test_production_explicit_cors_allowed():
    """Verify that explicit frontend domains pass validation in production mode."""
    settings = Settings(
        APP_ENV="production",
        CORS_ORIGINS="https://ai-knowledge-base.onrender.com",
    )
    assert settings.CORS_ORIGINS == ["https://ai-knowledge-base.onrender.com"]
    assert settings.APP_ENV == "production"
