"""tRPC routers."""
from ...trpc import create_router
from .diagram import diagram_router

# Create main app router
app_router = create_router()

# Merge routers
app_router.merge("diagram", diagram_router)

__all__ = ['app_router', 'diagram_router']