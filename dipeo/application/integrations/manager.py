"""Integration management functionality."""

import json
from pathlib import Path

import yaml

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import PROVIDER_REGISTRY
from dipeo.config.base_logger import get_module_logger
from dipeo.infrastructure.integrations.drivers.integrated_api.registry import ProviderRegistry

logger = get_module_logger(__name__)


class IntegrationsManager:
    """Manages API integrations and providers."""

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self.provider_registry: ProviderRegistry = registry.resolve(PROVIDER_REGISTRY)

    async def initialize_workspace(self, path: str) -> bool:
        try:
            workspace_path = Path(path)
            workspace_path.mkdir(parents=True, exist_ok=True)

            example_provider = workspace_path / "example"
            example_provider.mkdir(exist_ok=True)
            manifest = {
                "name": "example",
                "version": "1.0.0",
                "description": "Example API provider",
                "base_url": "https://api.example.com",
                "authentication": {
                    "type": "bearer",
                    "header": "Authorization",
                },
                "operations": [],
            }

            with open(example_provider / "provider.yaml", "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)

            logger.info(f"Initialized integrations workspace at {workspace_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize workspace: {e}")
            return False

    async def validate_providers(self, path: str, provider: str | None = None) -> bool:
        try:
            workspace_path = Path(path)

            if provider:
                provider_path = workspace_path / provider / "provider.yaml"
                if not provider_path.exists():
                    provider_path = workspace_path / provider / "provider.yml"
                if not provider_path.exists():
                    provider_path = workspace_path / provider / "provider.json"

                if provider_path.exists():
                    return await self._validate_manifest(provider_path)
                else:
                    logger.error(f"Provider manifest not found: {provider}")
                    return False
            else:
                success = True
                for provider_dir in workspace_path.iterdir():
                    if provider_dir.is_dir():
                        for manifest_name in ["provider.yaml", "provider.yml", "provider.json"]:
                            manifest_path = provider_dir / manifest_name
                            if manifest_path.exists():
                                if not await self._validate_manifest(manifest_path):
                                    success = False
                                break
                return success

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    async def import_openapi(
        self,
        openapi_path: str,
        name: str,
        output: str | None = None,
        base_url: str | None = None,
    ) -> bool:
        try:
            with open(openapi_path) as f:
                if openapi_path.endswith(".json"):
                    spec = json.load(f)
                else:
                    spec = yaml.safe_load(f)

            if not base_url and "servers" in spec and spec["servers"]:
                base_url = spec["servers"][0]["url"]

            manifest = {
                "name": name,
                "version": spec.get("info", {}).get("version", "1.0.0"),
                "description": spec.get("info", {}).get("description", ""),
                "base_url": base_url or "https://api.example.com",
                "operations": [],
            }

            for path, path_item in spec.get("paths", {}).items():
                for method, operation in path_item.items():
                    if method in ["get", "post", "put", "patch", "delete"]:
                        manifest["operations"].append(
                            {
                                "id": operation.get("operationId", f"{method}_{path}"),
                                "name": operation.get("summary", f"{method.upper()} {path}"),
                                "description": operation.get("description", ""),
                                "method": method.upper(),
                                "path": path,
                            }
                        )

            output_dir = Path(output or "./integrations") / name
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_dir / "provider.yaml", "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)

            logger.info(f"Imported OpenAPI spec as provider: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to import OpenAPI spec: {e}")
            return False

    async def test_provider(
        self,
        provider: str,
        operation: str | None = None,
        config: str | None = None,
        record: bool = False,
        replay: bool = False,
    ) -> bool:
        try:
            provider_obj = await self.provider_registry.get_provider(provider)
            if not provider_obj:
                logger.error(f"Provider not found: {provider}")
                return False

            test_config = {}
            if config:
                test_config = json.loads(config)

            if operation:
                result = await provider_obj.test_operation(operation, test_config, record, replay)
            else:
                result = await provider_obj.test_all_operations(test_config, record, replay)

            return result

        except Exception as e:
            logger.error(f"Provider test failed: {e}")
            return False

    async def setup_claude_code_sync(
        self,
        watch_todos: bool = False,
        sync_mode: str = "off",
        output_dir: str | None = None,
        auto_execute: bool = False,
        debounce: float = 2.0,
        timeout: int | None = None,
    ) -> bool:
        try:
            # TODO: Integrate with Claude Code monitoring - currently just logs configuration
            logger.info(
                f"Claude Code sync configured: mode={sync_mode}, "
                f"watch_todos={watch_todos}, auto_execute={auto_execute}"
            )

            if sync_mode == "watch":
                logger.info("Started watching Claude Code TODOs...")
                # TODO: Implement watcher here

            return True

        except Exception as e:
            logger.error(f"Failed to setup Claude Code sync: {e}")
            return False

    async def _validate_manifest(self, manifest_path: Path) -> bool:
        try:
            with open(manifest_path) as f:
                if manifest_path.suffix == ".json":
                    manifest = json.load(f)
                else:
                    manifest = yaml.safe_load(f)

            required = ["name", "version", "base_url"]
            for field in required:
                if field not in manifest:
                    logger.error(f"Missing required field '{field}' in {manifest_path}")
                    return False

            logger.info(f"✅ Valid: {manifest_path}")
            return True

        except Exception as e:
            logger.error(f"Invalid manifest {manifest_path}: {e}")
            return False
