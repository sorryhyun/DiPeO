"""Provider utilities for testing and overrides."""

from typing import Any

from dependency_injector import providers


def create_provider_overrides(**overrides: Any) -> dict[str, providers.Provider]:
    """
    Create provider overrides for testing.

    Example:
        overrides = create_provider_overrides(
            llm_service=mock_llm_service,
            file_service=mock_file_service
        )
        container.override_providers(**overrides)
    """
    provider_overrides = {}

    for name, value in overrides.items():
        if callable(value) and not isinstance(value, type):
            # It's a factory function
            provider_overrides[name] = providers.Factory(value)
        elif isinstance(value, type):
            # It's a class
            provider_overrides[name] = providers.Singleton(value)
        else:
            # It's an instance
            provider_overrides[name] = providers.Object(value)

    return provider_overrides


class MockServiceFactory:
    """Factory for creating mock services that implement protocols."""

    @staticmethod
    def create_mock_llm_service():
        """Create a mock LLM service."""
        from unittest.mock import AsyncMock, Mock

        mock = Mock()
        mock.initialize = AsyncMock()
        mock.complete = AsyncMock(return_value="Mock response")
        mock.get_token_usage = Mock(return_value={"prompt": 10, "completion": 20})
        return mock

    @staticmethod
    def create_mock_file_service():
        """Create a mock file service."""
        from unittest.mock import AsyncMock, Mock

        mock = Mock()
        mock.read_file = AsyncMock(return_value="Mock content")
        mock.write_file = AsyncMock()
        mock.exists = AsyncMock(return_value=True)
        mock.list_files = AsyncMock(return_value=["file1.txt", "file2.txt"])
        return mock

    @staticmethod
    def create_mock_api_key_service():
        """Create a mock API key service."""
        from unittest.mock import Mock

        mock = Mock()
        mock.get_api_key = Mock(return_value={"key": "mock-key", "service": "openai"})
        mock.list_api_keys = Mock(return_value=[{"id": "1", "name": "Test Key"}])
        mock.validate_api_key = Mock(return_value=True)
        return mock
