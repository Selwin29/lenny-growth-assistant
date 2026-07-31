"""Pydantic schemas for the health check endpoint."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "service": "Lenny Growth Assistant API",
        }
    })

    status: str
    service: str
