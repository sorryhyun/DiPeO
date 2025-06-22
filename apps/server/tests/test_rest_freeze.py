"""REST Endpoint Freeze Test

Purpose: Ensure no new REST endpoints are added to maintain architectural consistency.
After completing the GraphQL migration, this test serves as a guard to prevent
REST endpoint creep and ensure all new functionality uses GraphQL.

Only operational monitoring endpoints should remain as REST:
- Health checks (/api/health/*) - Required for Kubernetes probes
- Metrics (/metrics) - Required for Prometheus monitoring

All business logic must be implemented via GraphQL.
"""

import re
from pathlib import Path

import pytest


class TestRESTFreeze:
    """Test that no new REST endpoints are added during GraphQL migration."""

    def test_no_new_rest_endpoints(self):
        """Verify only allowed REST endpoints exist by checking route registration."""
        # Define allowed REST endpoints
        allowed_paths = {
            "/api/health",
            "/metrics",
        }

        # Check main.py for route registrations
        main_path = Path(__file__).parent.parent / "main.py"
        if not main_path.exists():
            pytest.skip("main.py not found")

        with open(main_path) as f:
            content = f.read()

        # Find all route inclusions
        router_pattern = r'app\.include_router\([^,]+,\s*prefix="([^"]+)"'
        route_pattern = r'@app\.(get|post|put|delete|patch)\("([^"]+)"'

        routes_found = []

        # Find router inclusions
        for match in re.finditer(router_pattern, content):
            prefix = match.group(1)
            if not prefix.startswith("/graphql"):
                routes_found.append(prefix)

        # Find direct route decorators
        for match in re.finditer(route_pattern, content):
            path = match.group(2)
            if not path.startswith("/graphql"):
                routes_found.append(path)

        # Check each found route
        for route in routes_found:
            # Skip documentation-related routes
            if route in ["/", "/docs", "/redoc", "/openapi.json"]:
                continue

            # Check if it's an allowed route or starts with an allowed prefix
            is_allowed = any(
                route == allowed or route.startswith(allowed.rstrip("/") + "/")
                for allowed in allowed_paths
            )

            assert is_allowed, (
                f"Unexpected REST endpoint found: {route}. "
                f"Only allowed endpoints are: {allowed_paths}. "
                f"All new functionality should be implemented via GraphQL."
            )

    def test_health_endpoint_exists(self):
        """Ensure health endpoint is available via GraphQL for monitoring."""
        # Health is now provided via GraphQL, not REST
        # Check that GraphQL schema includes health query
        queries_path = (
            Path(__file__).parent.parent / "src" / "dipeo_server" / "api" / "queries.py"
        )
        if not queries_path.exists():
            pytest.skip("queries.py not found")

        with open(queries_path) as f:
            content = f.read()

        # Verify health query exists in GraphQL schema
        assert "def health" in content, "Health query must be defined"
        assert "@strawberry.field" in content, "Health must be a GraphQL field"

        # For K8s compatibility, metrics endpoint still exists as REST
        main_path = Path(__file__).parent.parent / "main.py"
        if main_path.exists():
            with open(main_path) as f:
                main_content = f.read()
            assert "/metrics" in main_content, (
                "Metrics endpoint must exist for Prometheus"
            )

    def test_graphql_endpoint_exists(self):
        """Ensure GraphQL endpoint is properly configured as the primary API."""
        main_path = Path(__file__).parent.parent / "main.py"
        if not main_path.exists():
            pytest.skip("main.py not found")

        with open(main_path) as f:
            content = f.read()

        # Check that GraphQL is configured
        assert "GraphQL" in content, "GraphQL must be imported"
        assert "/graphql" in content, "GraphQL endpoint must be configured at /graphql"
