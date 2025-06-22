import os
import logging

from fastapi import FastAPI, Request
from fastapi.responses import Response
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

from dipeo_server.api.middleware import setup_middleware

from dipeo_server.core.context import lifespan

from dipeo_server.api.schema import create_graphql_router
from dipeo_server.api.context import get_graphql_context



app = FastAPI(
    title="DiPeO Backend API",
    description="API server for DiPeO visual programming environment",
    lifespan=lifespan
)

setup_middleware(app)

graphql_router = create_graphql_router(context_getter=get_graphql_context)
app.include_router(graphql_router, prefix="")
logger.info("GraphQL endpoint enabled at /graphql")

logger.info("All API operations are available via GraphQL at /graphql")




@app.get("/metrics")
async def metrics(request: Request):
    accept_header = request.headers.get("accept", "")
    
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        
        if "application/json" in accept_header:
            metrics_data = generate_latest().decode('utf-8')
            return {
                "metrics": metrics_data,
                "format": "prometheus",
                "message": "Metrics in Prometheus format"
            }
        
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    except ImportError:
        return {"message": "Prometheus client not installed. Install with: pip install prometheus-client"}

def start():
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    
    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 8000))}"]
    
    config.workers = int(os.environ.get("WORKERS", 4))
    
    redis_url = os.environ.get("REDIS_URL")
    if config.workers > 1 and not redis_url:
        logger.warning(
            "Running with multiple workers without Redis. "
            "GraphQL subscriptions require Redis for multi-worker support."
        )
    
    config.graceful_timeout = 30.0
    
    config.accesslog = "-"
    config.errorlog = "-"
    
    config.keep_alive_timeout = 75.0
    
    config.h2_max_concurrent_streams = 100
    
    if os.environ.get("RELOAD", "false").lower() == "true":
        logger.warning("Hot reload is not supported with Hypercorn. Please restart the server manually for changes.")
    
    asyncio.run(serve(app, config))

if __name__ == "__main__":
    start()