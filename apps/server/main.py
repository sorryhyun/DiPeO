import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response

# Load environment variables first
load_dotenv()

# Set up logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Reduce noisy debug logging
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("hypercorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Use consolidated app context
from dipeo_server.api.graphql.schema import (
    create_unified_graphql_router as create_graphql_router,
)
from dipeo_server.application.app_context import app_context

logger.info("🚀 Using UNIFIED architecture with direct streaming")

from dipeo_server.api.graphql.context import get_graphql_context
from dipeo_server.api.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await app_context.startup()
    yield
    await app_context.shutdown()


app = FastAPI(
    title="DiPeO Backend API",
    description="API server for DiPeO visual programming environment",
    lifespan=lifespan
)

setup_middleware(app)

graphql_router = create_graphql_router(context_getter=get_graphql_context)
app.include_router(graphql_router, prefix="")


@app.get("/metrics")
async def metrics(request: Request):
    accept_header = request.headers.get("accept", "")

    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

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

    from hypercorn.asyncio import serve
    from hypercorn.config import Config

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
