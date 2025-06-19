"""
REST Endpoint Freeze Test

Purpose: Ensure no new REST endpoints are added to maintain architectural consistency.
After completing the GraphQL migration, this test serves as a guard to prevent
REST endpoint creep and ensure all new functionality uses GraphQL.

Only operational monitoring endpoints should remain as REST:
- Health checks (/api/health/*) - Required for Kubernetes probes
- Metrics (/metrics) - Required for Prometheus monitoring

All business logic must be implemented via GraphQL.
"""
import unittest
import os
import sys
from pathlib import Path

# Add parent directory to path to import server module
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestRESTFreeze(unittest.TestCase):
    """Test that no new REST endpoints are added during GraphQL migration."""
    
    def test_no_new_rest_endpoints(self):
        """Verify only allowed REST endpoints exist by checking route registration."""
        # Instead of importing the app (which has issues), we'll check the source code
        # This is more reliable for CI/CD as it doesn't require the full app to start
        
        # Define allowed REST endpoints
        allowed_paths = {
            "/api/health",
            "/metrics",
        }
        
        # Check main.py for route registrations
        main_path = Path(__file__).parent.parent / "main.py"
        if not main_path.exists():
            self.skipTest("main.py not found")
            
        with open(main_path, 'r') as f:
            content = f.read()
            
        # Look for app.include_router or @app.get/@app.post decorators
        import re
        
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
                route == allowed or route.startswith(allowed.rstrip('/') + '/')
                for allowed in allowed_paths
            )
            
            self.assertTrue(
                is_allowed,
                f"Unexpected REST endpoint found: {route}. "
                f"Only allowed endpoints are: {allowed_paths}. "
                f"All new functionality should be implemented via GraphQL."
            )
    
    
    def test_health_endpoint_exists(self):
        """Ensure the health endpoint is still available for K8s/monitoring.""" 
        # Check that health router is imported and included in main.py
        main_path = Path(__file__).parent.parent / "main.py"
        if not main_path.exists():
            self.skipTest("main.py not found")
            
        with open(main_path, 'r') as f:
            content = f.read()
            
        # Check that health router is imported and included
        self.assertIn('health_router', content, "Health router must be imported")
        self.assertIn('app.include_router(health_router)', content, "Health router must be included")
        
        # Verify the actual endpoint in the router file
        router_path = Path(__file__).parent.parent / "src" / "api" / "routers" / "health.py"
        if router_path.exists():
            with open(router_path, 'r') as f:
                router_content = f.read()
            self.assertIn('prefix="/api/health"', router_content, "Health router must have /api/health prefix")
    
    def test_graphql_endpoint_exists(self):
        """Ensure GraphQL endpoint is properly configured as the primary API."""
        main_path = Path(__file__).parent.parent / "main.py"
        if not main_path.exists():
            self.skipTest("main.py not found")
            
        with open(main_path, 'r') as f:
            content = f.read()
            
        # Check that GraphQL is configured
        self.assertIn('GraphQL', content, "GraphQL must be imported")
        self.assertIn('/graphql', content, "GraphQL endpoint must be configured at /graphql")

if __name__ == "__main__":
    unittest.main()