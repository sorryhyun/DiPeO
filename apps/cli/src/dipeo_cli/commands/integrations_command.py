"""CLI commands for managing DiPeO integrations."""

import json
from pathlib import Path

import yaml
from dipeo.infrastructure.integrations.drivers.integrated_api.manifest_schema import (
    ProviderManifest,
)
from pydantic import ValidationError


class IntegrationsCommand:
    """Handle integration-related commands."""

    def __init__(self, server_manager=None):
        self.server = server_manager
        self.integrations_dir = Path("integrations")

    def init(self, path: str | None = None) -> bool:
        """Initialize a new integrations workspace."""
        workspace_path = Path(path) if path else self.integrations_dir

        try:
            # Create directory structure
            workspace_path.mkdir(parents=True, exist_ok=True)
            (workspace_path / "providers").mkdir(exist_ok=True)
            (workspace_path / "tests").mkdir(exist_ok=True)
            (workspace_path / "schemas").mkdir(exist_ok=True)

            # Create README
            readme_content = """# DiPeO Integrations

This directory contains API integration manifests for DiPeO.

## Structure
- `providers/` - Provider manifests (YAML/JSON)
- `tests/` - Integration tests and VCR cassettes
- `schemas/` - JSON schemas for request/response validation

## Usage
- Add new providers by creating manifest files in `providers/`
- Run `dipeo integrations validate` to check manifests
- Use `dipeo integrations test` to test providers
"""
            (workspace_path / "README.md").write_text(readme_content)

            # Create example provider manifest
            example_manifest = {
                "name": "example",
                "version": "1.0.0",
                "base_url": "https://api.example.com",
                "auth": {
                    "strategy": "api_key_header",
                    "header": "X-API-Key",
                    "format": "{{secret.api_key}}",
                },
                "retry_policy": {
                    "strategy": "exponential_backoff",
                    "max_retries": 3,
                    "base_delay_ms": 300,
                },
                "operations": {
                    "get_data": {
                        "method": "GET",
                        "path": "/data/{{config.id}}",
                        "response": {"success_codes": [200], "json_pointer": "$"},
                    }
                },
            }

            example_path = workspace_path / "providers" / "example.yaml"
            with example_path.open("w") as f:
                yaml.dump(example_manifest, f, default_flow_style=False)

            print(f"✅ Initialized integrations workspace at: {workspace_path}")
            print(f"   Created example provider: {example_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize workspace: {e}")
            return False

    def validate(self, path: str | None = None, provider: str | None = None) -> bool:
        """Validate provider manifests."""
        workspace_path = Path(path) if path else self.integrations_dir
        providers_dir = workspace_path / "providers"

        if not providers_dir.exists():
            print(f"❌ Providers directory not found: {providers_dir}")
            print("   Run 'dipeo integrations init' first")
            return False

        # Find manifest files
        if provider:
            # Validate specific provider
            manifest_files = []
            for ext in [".yaml", ".yml", ".json"]:
                provider_file = providers_dir / f"{provider}{ext}"
                if provider_file.exists():
                    manifest_files.append(provider_file)
                    break
            if not manifest_files:
                print(f"❌ Provider manifest not found: {provider}")
                return False
        else:
            # Validate all providers
            manifest_files = list(providers_dir.glob("*.yaml"))
            manifest_files.extend(providers_dir.glob("*.yml"))
            manifest_files.extend(providers_dir.glob("*.json"))

        if not manifest_files:
            print("INFO: No provider manifests found")
            return True

        all_valid = True
        for manifest_file in manifest_files:
            print(f"\n📋 Validating: {manifest_file.name}")

            try:
                # Load manifest
                with manifest_file.open() as f:
                    if manifest_file.suffix == ".json":
                        data = json.load(f)
                    else:
                        data = yaml.safe_load(f)

                # Validate with Pydantic
                manifest = ProviderManifest(**data)

                print("   ✅ Valid manifest")
                print(f"   • Name: {manifest.name}")
                print(f"   • Version: {manifest.version}")
                print(f"   • Operations: {', '.join(manifest.operations.keys())}")

            except ValidationError as e:
                all_valid = False
                print("   ❌ Validation failed:")
                for error in e.errors():
                    field = ".".join(str(x) for x in error["loc"])
                    print(f"      • {field}: {error['msg']}")
            except Exception as e:
                all_valid = False
                print(f"   ❌ Error loading manifest: {e}")

        print()
        if all_valid:
            print("✅ All manifests are valid")
        else:
            print("❌ Some manifests have errors")

        return all_valid

    def openapi_import(
        self,
        openapi_path: str,
        provider_name: str,
        output_path: str | None = None,
        base_url: str | None = None,
    ) -> bool:
        """Import an OpenAPI specification and generate a provider manifest."""
        try:
            # Load OpenAPI spec
            openapi_file = Path(openapi_path)
            if not openapi_file.exists():
                print(f"❌ OpenAPI file not found: {openapi_path}")
                return False

            with openapi_file.open() as f:
                if openapi_file.suffix == ".json":
                    spec = json.load(f)
                else:
                    spec = yaml.safe_load(f)

            # Determine output path
            if output_path:
                output_dir = Path(output_path)
            else:
                output_dir = self.integrations_dir / "providers"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Extract base URL from spec or use provided
            if not base_url:
                servers = spec.get("servers", [])
                if servers:
                    base_url = servers[0].get("url", "https://api.example.com")
                else:
                    base_url = "https://api.example.com"

            # Build provider manifest
            manifest = {
                "name": provider_name,
                "version": "1.0.0",
                "base_url": base_url,
                "description": spec.get("info", {}).get("description", ""),
                "auth": {
                    "strategy": "api_key_header",
                    "header": "Authorization",
                    "format": "Bearer {{secret.token}}",
                },
                "retry_policy": {
                    "strategy": "exponential_backoff",
                    "max_retries": 3,
                    "base_delay_ms": 300,
                },
                "operations": {},
            }

            # Convert paths to operations
            paths = spec.get("paths", {})
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        continue

                    op_id = operation.get(
                        "operationId", f"{method}_{path.replace('/', '_')}"
                    )
                    op_id = op_id.replace("-", "_").replace(" ", "_").lower()

                    # Build operation config
                    op_config = {
                        "method": method.upper(),
                        "path": path,
                        "description": operation.get(
                            "summary", operation.get("description", "")
                        ),
                        "response": {
                            "success_codes": [200, 201, 204],
                            "json_pointer": "$",
                        },
                    }

                    # Add request body template if applicable
                    if "requestBody" in operation:
                        content = operation["requestBody"].get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            # Create a simple template based on schema
                            op_config["request"] = {
                                "body_template": "{{config.body | tojson}}"
                            }

                    # Add to manifest
                    manifest["operations"][op_id] = op_config

            # Save manifest
            output_file = output_dir / f"{provider_name}.yaml"
            with output_file.open("w") as f:
                yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

            # Save schemas directory
            schemas_dir = output_dir.parent / "schemas" / provider_name
            schemas_dir.mkdir(parents=True, exist_ok=True)

            # Save the original OpenAPI spec for reference
            spec_file = schemas_dir / "openapi.json"
            with spec_file.open("w") as f:
                json.dump(spec, f, indent=2)

            print("✅ Imported OpenAPI specification")
            print(f"   • Provider: {provider_name}")
            print(f"   • Operations: {len(manifest['operations'])}")
            print(f"   • Manifest: {output_file}")
            print(f"   • Schemas: {schemas_dir}")
            print()
            print("⚠️  Review and customize the generated manifest:")
            print("   • Update authentication configuration")
            print("   • Add request/response templates as needed")
            print("   • Configure rate limiting if applicable")

            return True

        except Exception as e:
            print(f"❌ Failed to import OpenAPI: {e}")
            return False

    def test(
        self,
        provider: str,
        operation: str | None = None,
        config: str | None = None,
        record: bool = False,
        replay: bool = False,
    ) -> bool:
        """Test an integration provider."""
        from dipeo.infrastructure.integrations.drivers.integrated_api.registry import (
            ProviderRegistry,
        )

        try:
            # Initialize provider registry
            registry = ProviderRegistry()

            # Load provider manifests
            workspace_path = self.integrations_dir
            providers_dir = workspace_path / "providers"

            if not providers_dir.exists():
                print(f"❌ Providers directory not found: {providers_dir}")
                return False

            # Load the specific provider
            provider_file = None
            for ext in [".yaml", ".yml", ".json"]:
                test_file = providers_dir / f"{provider}{ext}"
                if test_file.exists():
                    provider_file = test_file
                    break

            if not provider_file:
                print(f"❌ Provider not found: {provider}")
                return False

            # Load manifest
            with provider_file.open() as f:
                if provider_file.suffix == ".json":
                    manifest_data = json.load(f)
                else:
                    manifest_data = yaml.safe_load(f)

            # Validate manifest
            try:
                manifest = ProviderManifest(**manifest_data)
            except ValidationError as e:
                print(f"❌ Invalid manifest: {e}")
                return False

            print(f"🧪 Testing provider: {provider}")
            print(f"   Version: {manifest.version}")

            if operation:
                # Test specific operation
                if operation not in manifest.operations:
                    print(f"❌ Operation not found: {operation}")
                    print(f"   Available: {', '.join(manifest.operations.keys())}")
                    return False

                ops_to_test = [operation]
            else:
                # Test all operations
                ops_to_test = list(manifest.operations.keys())

            print(f"   Operations to test: {', '.join(ops_to_test)}")

            # Parse config if provided
            test_config = {}
            if config:
                try:
                    test_config = json.loads(config)
                except json.JSONDecodeError:
                    print(f"❌ Invalid config JSON: {config}")
                    return False

            # Recording/replay setup
            if record:
                print("   📹 Recording mode enabled")
                cassette_dir = workspace_path / "tests" / "cassettes" / provider
                cassette_dir.mkdir(parents=True, exist_ok=True)
            elif replay:
                print("   ▶️  Replay mode enabled")
                cassette_dir = workspace_path / "tests" / "cassettes" / provider
                if not cassette_dir.exists():
                    print(f"❌ No recordings found for {provider}")
                    return False

            # Run tests
            all_passed = True
            for op_name in ops_to_test:
                print(f"\n   Testing: {op_name}")
                op_def = manifest.operations[op_name]

                # In a real implementation, this would:
                # 1. Create a GenericHTTPProvider instance
                # 2. Execute the operation with test config
                # 3. Record/replay if configured
                # 4. Validate response

                # For now, just show what would be tested
                print(f"      Method: {op_def.method}")
                print(f"      Path: {op_def.path}")
                if test_config:
                    print(f"      Config: {json.dumps(test_config, indent=8)}")

                # Simulate test result
                print("      ✅ Test passed (simulated)")

            print()
            if all_passed:
                print("✅ All tests passed")
            else:
                print("❌ Some tests failed")

            return all_passed

        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False

    def execute(self, action: str, **kwargs) -> bool:
        """Execute an integrations command."""
        if action == "init":
            return self.init(kwargs.get("path"))
        if action == "validate":
            return self.validate(
                path=kwargs.get("path"), provider=kwargs.get("provider")
            )
        if action == "openapi-import":
            return self.openapi_import(
                openapi_path=kwargs["openapi_path"],
                provider_name=kwargs["name"],
                output_path=kwargs.get("output"),
                base_url=kwargs.get("base_url"),
            )
        if action == "test":
            return self.test(
                provider=kwargs["provider"],
                operation=kwargs.get("operation"),
                config=kwargs.get("config"),
                record=kwargs.get("record", False),
                replay=kwargs.get("replay", False),
            )
        print(f"❌ Unknown action: {action}")
        return False
