from datetime import datetime, timezone
from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health status response."""

    status: str = Field(default="ok", description="Overall system health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Active runtime environment")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of the health check",
    )


class ReadinessResponse(BaseModel):
    """Schema for readiness probe response."""

    status: str = Field(default="ready", description="Readiness state of the service")
    storage_ready: bool = Field(default=True, description="Whether local storage paths are accessible")
    services: Dict[str, str] = Field(
        default_factory=lambda: {"api": "up", "storage": "mounted"},
        description="Status breakdown of subcomponents",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC ISO timestamp of the readiness check",
    )
