"""REST API interfaces for essential endpoints."""

from fastapi import APIRouter

# Create main health router
health_router = APIRouter(prefix="/api/health", tags=["health"])

@health_router.get("")
async def health_check():
    return {
        "status": "healthy",
        "service": "DiPeO Backend API"
    }

@health_router.get("/live")
async def liveness():
    return {"status": "alive"}

@health_router.get("/ready")
async def readiness():
    return {"status": "ready"}