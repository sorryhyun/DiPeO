import os
import sys
import logging
from fastapi import FastAPI, Request
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

logger = logging.getLogger(__name__)

# Import routers and middleware
from .src.api.routers import (
    diagram_router,
    apikeys_router,
    files_router,
    conversations_router,
    websocket_router,
    models_router,
    health_router
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
app.include_router(health_router)
app.include_router(diagram_router)
app.include_router(apikeys_router)
app.include_router(files_router)
app.include_router(conversations_router)
app.include_router(websocket_router)
app.include_router(models_router)


# Health check endpoint moved to diagram router at /api/diagrams/health


# Metrics endpoint
@app.get("/metrics")
async def metrics(request: Request):
    """Expose Prometheus metrics with content negotiation support."""
    # Support content negotiation for tests
    accept_header = request.headers.get("accept", "")
    
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        # Return JSON format for tests
        if "application/json" in accept_header:
            metrics_data = generate_latest().decode('utf-8')
            return {
                "metrics": metrics_data,
                "format": "prometheus",
                "message": "Metrics in Prometheus format"
            }
        
        # Default to Prometheus text format
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    except ImportError:
        # If prometheus_client is not installed, return a simple message
        return {"message": "Prometheus client not installed. Install with: pip install prometheus-client"}

def start():
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    
    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 8000))}"]
    
    # Multi-worker support for better parallel execution
    config.workers = int(os.environ.get("WORKERS", 4))
    
    # Graceful timeout for WebSocket connections
    config.graceful_timeout = 30.0
    
    # Access and error logging
    config.accesslog = "-"
    config.errorlog = "-"
    
    # Keep alive for long-running WebSocket connections
    config.keep_alive_timeout = 75.0
    
    # Enable HTTP/2 for better WebSocket multiplexing
    config.h2_max_concurrent_streams = 100
    
    # Note: Hypercorn doesn't support hot reload like uvicorn
    # For development, you'll need to restart the server manually
    if os.environ.get("RELOAD", "false").lower() == "true":
        logger.warning("Hot reload is not supported with Hypercorn. Please restart the server manually for changes.")
    
    asyncio.run(serve(app, config))

if __name__ == "__main__":
    start()