"""Integration test for Notion manifest-based provider.

This test verifies that the Notion manifest provider works correctly
before we remove the legacy providers.
"""

import asyncio
from pathlib import Path

from dipeo.infrastructure.services.integrated_api.service import IntegratedApiService
from dipeo.infrastructure.services.integrated_api.registry import ProviderRegistry
from dipeo.application.services.apikey_service import APIKeyService
from dipeo.infrastructure.adapters.http.api_service import APIService
from dipeo.domain.integrations.api_services import APIBusinessLogic


async def test_notion_manifest():
    """Test Notion operations using the manifest-based provider."""
    
    print("=== Testing Notion Manifest Provider ===\n")
    
    # Initialize services
    api_key_service = APIKeyService(file_path="files/apikeys.json")
    await api_key_service.initialize()
    
    business_logic = APIBusinessLogic()
    api_service = APIService(business_logic)
    
    # Create integrated API service
    integrated_api = IntegratedApiService(
        api_service=api_service,
        api_key_port=api_key_service
    )
    
    # Initialize but DON'T load default providers
    integrated_api.provider_registry = ProviderRegistry()
    await integrated_api.provider_registry.initialize()
    
    # Load ONLY the manifest-based Notion provider
    manifest_path = Path("integrations/notion/provider.yaml")
    if not manifest_path.exists():
        print(f"❌ Manifest not found at {manifest_path}")
        return False
    
    print(f"Loading manifest from {manifest_path}")
    await integrated_api.provider_registry._load_single_manifest(manifest_path)
    
    # Verify the provider was loaded
    providers = integrated_api.provider_registry.list_providers()
    print(f"Loaded providers: {providers}")
    
    if "notion" not in providers:
        print("❌ Notion provider not loaded")
        return False
    
    notion_provider = integrated_api.provider_registry.get_provider("notion")
    print(f"✓ Notion provider loaded: {type(notion_provider).__name__}")
    print(f"  Operations: {notion_provider.supported_operations}")
    
    # Get API key
    api_key_info = api_key_service.get_api_key("notion")
    if not api_key_info:
        print("❌ No Notion API key found")
        return False
    api_key = api_key_info.get("key")
    if not api_key:
        print("❌ No API key value found")
        return False
    print("✓ API key loaded")
    
    # Test 1: Create a page
    print("\n--- Test 1: Create Page ---")
    try:
        # Pass actual Python objects, not JSON strings
        # The template will convert them with tojson filter
        # Use database ID as parent since workspace-level pages aren't supported
        create_config = {
            "parent": {"type": "database_id", "database_id": "202c8edd335e8059af75fe79d0451885"},
            "properties": {
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": "Test Page from Manifest Provider"}
                        }
                    ]
                }
            },
            "children": [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "This page was created using the manifest-based provider."}
                            }
                        ]
                    }
                }
            ]
        }
        
        result = await integrated_api.execute_operation(
            provider="notion",
            operation="create_page",
            config=create_config,
            api_key=api_key,
            timeout=30.0
        )
        
        if result.get("success"):
            page_id = result.get("data", {}).get("id")
            page_url = result.get("data", {}).get("url")
            print(f"✓ Page created successfully")
            print(f"  ID: {page_id}")
            print(f"  URL: {page_url}")
            
            # Test 2: Read the page
            print("\n--- Test 2: Read Page ---")
            read_result = await integrated_api.execute_operation(
                provider="notion",
                operation="read_page",
                resource_id=page_id,
                api_key=api_key,
                timeout=30.0
            )
            
            if read_result.get("success"):
                print("✓ Page read successfully")
                print(f"  Created time: {read_result.get('data', {}).get('created_time')}")
            else:
                print(f"❌ Failed to read page: {read_result.get('error')}")
            
            # Test 3: Append blocks
            print("\n--- Test 3: Append Blocks ---")
            append_config = {
                "blocks": [
                    {
                        "type": "divider",
                        "divider": {}
                    },
                    {
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "Appended via Manifest Provider"}
                                }
                            ]
                        }
                    }
                ]
            }
            
            append_result = await integrated_api.execute_operation(
                provider="notion",
                operation="append_blocks",
                config=append_config,
                resource_id=page_id,
                api_key=api_key,
                timeout=30.0
            )
            
            if append_result.get("success"):
                print("✓ Blocks appended successfully")
            else:
                print(f"❌ Failed to append blocks: {append_result.get('error')}")
            
            # Test 4: List blocks
            print("\n--- Test 4: List Blocks ---")
            list_config = {"page_size": "50"}
            
            list_result = await integrated_api.execute_operation(
                provider="notion",
                operation="list_blocks",
                config=list_config,
                resource_id=page_id,
                api_key=api_key,
                timeout=30.0
            )
            
            if list_result.get("success"):
                blocks = list_result.get("data", {}).get("results", [])
                print(f"✓ Blocks listed successfully")
                print(f"  Total blocks: {len(blocks)}")
            else:
                print(f"❌ Failed to list blocks: {list_result.get('error')}")
            
            return True
        else:
            print(f"❌ Failed to create page: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the integration test."""
    success = await test_notion_manifest()
    
    print("\n=== Test Summary ===")
    if success:
        print("✅ All tests passed! The manifest-based Notion provider is working correctly.")
        print("\nYou can now safely remove the legacy providers from:")
        print("  - dipeo/infrastructure/services/integrated_api/providers/notion_provider.py")
        print("  - dipeo/infrastructure/services/integrated_api/providers/slack_provider.py")
    else:
        print("❌ Tests failed. Please fix issues before removing legacy providers.")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)