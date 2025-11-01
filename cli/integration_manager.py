"""Integration management for CLI."""

from dipeo.application.bootstrap import Container
from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


class IntegrationCommandManager:
    """Manages API integration commands for CLI."""

    def __init__(self, container: Container):
        """Initialize integration command manager.

        Args:
            container: Dependency injection container
        """
        self.container = container
        self.registry = container.registry

    async def manage_integrations(self, action: str, **kwargs) -> bool:
        """Manage API integrations.

        Args:
            action: The action to perform (init, validate, openapi-import, test, claude-code)
            **kwargs: Action-specific parameters

        Returns:
            True if action completed successfully, False otherwise
        """
        try:
            from dipeo.application.integrations.manager import IntegrationsManager

            manager = IntegrationsManager(self.registry)

            if action == "init":
                path = kwargs.get("path", "./integrations")
                result = await manager.initialize_workspace(path)

            elif action == "validate":
                path = kwargs.get("path", "./integrations")
                provider = kwargs.get("provider")
                result = await manager.validate_providers(path, provider)

            elif action == "openapi-import":
                result = await manager.import_openapi(
                    kwargs["openapi_path"],
                    kwargs["name"],
                    kwargs.get("output"),
                    kwargs.get("base_url"),
                )

            elif action == "test":
                result = await manager.test_provider(
                    kwargs["provider"],
                    kwargs.get("operation"),
                    kwargs.get("config"),
                    kwargs.get("record", False),
                    kwargs.get("replay", False),
                )

            elif action == "claude-code":
                result = await manager.setup_claude_code_sync(
                    kwargs.get("watch_todos", False),
                    kwargs.get("sync_mode", "off"),
                    kwargs.get("output_dir"),
                    kwargs.get("auto_execute", False),
                    kwargs.get("debounce", 2.0),
                    kwargs.get("timeout"),
                )
            else:
                print(f"❌ Unknown action: {action}")
                return False

            return result

        except Exception as e:
            logger.error(f"Integration management failed: {e}")
            return False
