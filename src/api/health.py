# Exposes the '/health' endpoint

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Perform a basic health check for the API.

    Returns:
        str: A simple "ok" status message indicating the service is healthy.
    """
    return "ok"
