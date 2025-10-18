"""Health check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel

from ...db import supabase_client
from ...utils.logger import logger


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str
    version: str
    database: str
    details: dict = {}


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint.
    
    Checks:
    - Application is running
    - Database connection is healthy
    
    Returns:
        HealthResponse with status information
    """
    # Check database health
    db_healthy = await supabase_client.health_check()
    
    response = HealthResponse(
        status="healthy" if db_healthy else "degraded",
        version="0.1.0",
        database="connected" if db_healthy else "disconnected",
        details={
            "database_healthy": db_healthy,
        }
    )
    
    if not db_healthy:
        logger.warning(
            "Health check failed: database unhealthy",
            extra={
                "event_type": "health_check_degraded",
                "metadata": {"database": "disconnected"}
            }
        )
    
    return response


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check for Kubernetes/Docker.
    
    Returns 200 if the application is ready to serve traffic.
    Returns 503 if not ready (e.g., database not connected).
    
    Returns:
        Simple status message
    """
    db_healthy = await supabase_client.health_check()
    
    if not db_healthy:
        logger.warning(
            "Readiness check failed",
            extra={"event_type": "readiness_check_failed"}
        )
        return {"status": "not_ready", "reason": "database_unavailable"}
    
    return {"status": "ready"}


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness check for Kubernetes/Docker.
    
    Returns 200 if the application is alive (even if degraded).
    Should only fail if the application needs to be restarted.
    
    Returns:
        Simple status message
    """
    return {"status": "alive"}
