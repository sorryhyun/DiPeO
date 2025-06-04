import os
import sys
import logging
from fastapi import FastAPI
from fastapi.responses import Response
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import routers and middleware
from .src.api.routers import (
    diagram_router,
    apikeys_router,
    files_router,
    conversations_router,
    monitor_router
)
from .src.api.middleware import setup_middleware

# Import lifespan from dependencies
from .src.utils.dependencies import lifespan


# Create FastAPI app
app = FastAPI(
    title="DiPeO Backend API",
    description="API server for DiPeO visual programming environment",
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(diagram_router)
app.include_router(apikeys_router)
app.include_router(files_router)
app.include_router(conversations_router)
app.include_router(monitor_router)


# Health check endpoint moved to diagram router at /api/diagrams/health


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    except ImportError:
        # If prometheus_client is not installed, return a simple message
        return {"message": "Prometheus client not installed. Install with: pip install prometheus-client"}

def start():
    import uvicorn
    uvicorn.run(
        "apps.server.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=os.environ.get("RELOAD", "false").lower() == "true"
    )

if __name__ == "__main__":
    start()