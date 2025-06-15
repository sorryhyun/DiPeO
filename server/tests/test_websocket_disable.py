"""
Test WebSocket endpoint can be disabled via environment variable.
"""
import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestWebSocketDisable(unittest.TestCase):
    """Test WebSocket endpoint disable functionality."""
    
    def test_websocket_enabled_by_default(self):
        """Verify WebSocket is enabled by default."""
        # Import fresh to get default behavior
        import importlib
        import src.api.config
        importlib.reload(src.api.config)
        
        from src.api.config import ENABLE_WEBSOCKET, is_router_enabled
        
        self.assertTrue(ENABLE_WEBSOCKET, "WebSocket should be enabled by default")
        self.assertTrue(is_router_enabled("websocket"), "WebSocket router should be enabled by default")
    
    def test_websocket_can_be_disabled(self):
        """Verify WebSocket can be disabled via environment variable."""
        # Set the environment variable before importing
        with patch.dict(os.environ, {"DISABLE_WEBSOCKET": "true"}):
            # Reload the module to pick up new env var
            import importlib
            import src.api.config
            importlib.reload(src.api.config)
            
            from src.api.config import ENABLE_WEBSOCKET, is_router_enabled
            
            self.assertFalse(ENABLE_WEBSOCKET, "WebSocket should be disabled when DISABLE_WEBSOCKET=true")
            self.assertFalse(is_router_enabled("websocket"), "WebSocket router should be disabled")
            
            # Verify health endpoints are still enabled
            self.assertTrue(is_router_enabled("health"), "Health endpoints should remain enabled")
    
    def test_websocket_disable_case_insensitive(self):
        """Verify DISABLE_WEBSOCKET is case insensitive."""
        test_values = ["TRUE", "True", "true", "TrUe"]
        
        for value in test_values:
            with patch.dict(os.environ, {"DISABLE_WEBSOCKET": value}):
                import importlib
                import src.api.config
                importlib.reload(src.api.config)
                
                from src.api.config import ENABLE_WEBSOCKET
                
                self.assertFalse(
                    ENABLE_WEBSOCKET, 
                    f"WebSocket should be disabled when DISABLE_WEBSOCKET={value}"
                )
    
    def test_websocket_enabled_with_false_value(self):
        """Verify WebSocket remains enabled when DISABLE_WEBSOCKET is false."""
        test_values = ["false", "FALSE", "False", "0", "no", ""]
        
        for value in test_values:
            with patch.dict(os.environ, {"DISABLE_WEBSOCKET": value}):
                import importlib
                import src.api.config
                importlib.reload(src.api.config)
                
                from src.api.config import ENABLE_WEBSOCKET
                
                self.assertTrue(
                    ENABLE_WEBSOCKET,
                    f"WebSocket should be enabled when DISABLE_WEBSOCKET={value}"
                )
    
    def test_router_list_updates_correctly(self):
        """Verify ENABLED_ROUTERS set updates based on flags."""
        # Test with WebSocket enabled
        with patch.dict(os.environ, {"DISABLE_WEBSOCKET": "false"}):
            import importlib
            import src.api.config
            importlib.reload(src.api.config)
            
            from src.api.config import ENABLED_ROUTERS
            
            self.assertIn("health", ENABLED_ROUTERS, "Health should be in enabled routers")
            self.assertIn("websocket", ENABLED_ROUTERS, "WebSocket should be in enabled routers")
        
        # Test with WebSocket disabled
        with patch.dict(os.environ, {"DISABLE_WEBSOCKET": "true"}):
            importlib.reload(src.api.config)
            
            from src.api.config import ENABLED_ROUTERS
            
            self.assertIn("health", ENABLED_ROUTERS, "Health should still be in enabled routers")
            self.assertNotIn("websocket", ENABLED_ROUTERS, "WebSocket should not be in enabled routers")

if __name__ == "__main__":
    unittest.main()