"""API Router configuration for DiPeO server."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL

from dipeo.application.graphql import create_schema

from .context import get_request_context
from .mcp_sdk_server import create_info_router, create_messages_router
from .webhooks import router as webhook_router


def create_graphql_router(context_getter=None, container=None):
    """Create a GraphQL router with monitoring stream support."""
    from dipeo_server.app_context import get_container

    if not container:
        container = get_container()

    schema = create_schema(container.registry)

    return GraphQLRouter(
        schema,
        context_getter=context_getter,
        graphiql=True,
        subscription_protocols=[
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
        ],
        path="/graphql",
        multipart_uploads_enabled=True,
    )


def setup_routes(app: FastAPI):
    graphql_router = create_graphql_router(context_getter=get_request_context)
    app.include_router(graphql_router, prefix="")

    app.include_router(webhook_router)

    mcp_messages_router = create_messages_router()
    app.include_router(mcp_messages_router)

    mcp_info_router = create_info_router()
    app.include_router(mcp_info_router)

    # Mount static files for ChatGPT widgets
    widgets_dir = Path(__file__).parent.parent.parent.parent / "static" / "widgets"
    if widgets_dir.exists():
        app.mount("/widgets", StaticFiles(directory=str(widgets_dir)), name="widgets")
