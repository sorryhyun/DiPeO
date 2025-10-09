import os
import sys
import warnings
from contextlib import asynccontextmanager
from pathlib import Path

from dipeo_server.api.middleware import setup_middleware
from dipeo_server.api.router import setup_routes
from dipeo_server.app_context import initialize_container_async
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response

from dipeo.application.bootstrap import init_resources, shutdown_resources
from dipeo.infrastructure.logging_config import setup_logging


def setup_bundled_paths():
    """Set up paths for the bundled application if running as PyInstaller bundle."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundle_dir = Path(sys._MEIPASS)
        os.environ["DIPEO_BUNDLED"] = "1"
        exe_dir = Path(sys.executable).parent

        files_dir = exe_dir / "files"
        files_dir.mkdir(exist_ok=True)

        for subdir in [
            "uploads",
            "results",
            "conversation_logs",
            "prompts",
            "diagrams",
        ]:
            (files_dir / subdir).mkdir(exist_ok=True)

        data_dir = exe_dir / ".data"
        data_dir.mkdir(exist_ok=True)
        os.environ["DIPEO_BASE_DIR"] = str(exe_dir)

        print(f"[BUNDLED] Executable directory: {exe_dir}")
        print(f"[BUNDLED] DIPEO_BASE_DIR set to: {os.environ['DIPEO_BASE_DIR']}")
        print(f"[BUNDLED] Expected database path: {exe_dir / '.data' / 'dipeo_state.db'}")

        sys.path.insert(0, str(bundle_dir))
        os.chdir(exe_dir)
        print(f"[BUNDLED] Changed working directory to: {Path.cwd()}")


setup_bundled_paths()
load_dotenv()

warnings.filterwarnings("ignore", message="_type_definition is deprecated", category=UserWarning)
warnings.filterwarnings(
    "ignore",
    message="The config `workers` has no affect when using serve",
    category=Warning,
)
warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)
warnings.filterwarnings("ignore", message="Field name.*shadows an attribute", category=UserWarning)

log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = setup_logging(
    component="server",
    log_level=log_level,
    log_to_file=True,
    log_dir=".logs",
    console_output=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = await initialize_container_async()
    await init_resources(container)
    setup_routes(app)

    yield
    await shutdown_resources(container)


app = FastAPI(
    title="DiPeO Backend API",
    description="API server for DiPeO visual programming environment",
    lifespan=lifespan,
)

setup_middleware(app)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "dipeo-server"}


@app.get("/metrics")
async def metrics(request: Request):
    accept_header = request.headers.get("accept", "")

    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        if "application/json" in accept_header:
            metrics_data = generate_latest().decode("utf-8")
            return {
                "metrics": metrics_data,
                "format": "prometheus",
                "message": "Metrics in Prometheus format",
            }

        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return {
            "message": "Prometheus client not installed. Install with: pip install prometheus-client"
        }


def start():
    import asyncio

    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', '8000'))}"]
    config.workers = int(os.environ.get("WORKERS", "4"))

    redis_url = os.environ.get("DIPEO_REDIS_URL") or os.environ.get("REDIS_URL")
    if config.workers > 1 and not redis_url:
        logger.warning(
            "Running with multiple workers without Redis. "
            "GraphQL subscriptions require Redis for multi-worker support."
        )

    config.graceful_timeout = 30.0
    config.accesslog = None
    config.errorlog = "-"
    config.keep_alive_timeout = 75.0
    config.h2_max_concurrent_streams = 100

    if os.environ.get("RELOAD", "false").lower() == "true":
        logger.warning(
            "Hot reload is not supported with Hypercorn. Please restart the server manually for changes."
        )

    asyncio.run(serve(app, config))


if __name__ == "__main__":
    start()
