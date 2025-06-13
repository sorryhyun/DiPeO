from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "DiPeO Backend API"
    }

@router.get("/live")
async def liveness() -> Dict[str, str]:
    return {"status": "alive"}

@router.get("/ready")
async def readiness() -> Dict[str, str]:
    return {"status": "ready"}