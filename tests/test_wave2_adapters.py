"""Test script for Wave 2 domain port adapters."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.registry_tokens import (
    STATE_REPOSITORY,
    STATE_SERVICE,
    STATE_CACHE,
    MESSAGE_BUS,
    DOMAIN_EVENT_BUS,
    LLM_CLIENT,
    LLM_SERVICE,
    API_PROVIDER_REGISTRY,
    API_INVOKER,
)
from dipeo.application.wiring.port_v2_wiring import (
    wire_all_v2_services,
    get_feature_flag_status,
)
from dipeo.diagram_generated import (
    ExecutionID,
    DiagramID,
    Status,
    TokenUsage,
)


async def test_state_adapters(registry: ServiceRegistry) -> bool:
    """Test state management adapters."""
    print("\n=== Testing State Adapters ===")
    
    try:
        # Get services
        repository = registry.resolve(STATE_REPOSITORY)
        service = registry.resolve(STATE_SERVICE)
        cache = registry.resolve(STATE_CACHE)
        
        # Initialize if needed
        if hasattr(repository, 'initialize'):
            await repository.initialize()
        
        # Test execution creation
        exec_id = ExecutionID("test-exec-001")
        diagram_id = DiagramID("test-diagram-001")
        variables = {"test_var": "test_value"}
        
        # Create execution via service
        state = await service.start_execution(exec_id, diagram_id, variables)
        print(f"✓ Created execution: {state.id}")
        
        # Test node execution update
        await service.update_node_execution(
            str(exec_id),
            "node-001",
            {"result": "success"},
            Status.COMPLETED,
            token_usage=TokenUsage(input=10, output=20, total=30),
        )
        print("✓ Updated node execution")
        
        # Test retrieval
        retrieved_state = await service.get_execution_state(str(exec_id))
        assert retrieved_state is not None
        assert retrieved_state.id == exec_id
        print("✓ Retrieved execution state")
        
        # Test cache
        cached_state = await cache.get_state_from_cache(str(exec_id))
        if cached_state:
            print("✓ Cache working")
        
        # Test completion
        await service.finish_execution(
            str(exec_id),
            Status.COMPLETED,
        )
        print("✓ Finished execution")
        
        # Cleanup
        if hasattr(repository, 'cleanup'):
            await repository.cleanup()
        
        return True
        
    except Exception as e:
        print(f"✗ State adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_messaging_adapters(registry: ServiceRegistry) -> bool:
    """Test messaging adapters."""
    print("\n=== Testing Messaging Adapters ===")
    
    try:
        # Get services
        message_bus = registry.resolve(MESSAGE_BUS)
        event_bus = registry.resolve(DOMAIN_EVENT_BUS)
        
        # Initialize
        await message_bus.initialize()
        await event_bus.initialize()
        
        # Test message bus
        received_messages = []
        
        async def test_handler(message):
            received_messages.append(message)
        
        # Register connection
        await message_bus.register_connection("test-conn-001", test_handler)
        print("✓ Registered connection")
        
        # Subscribe to execution
        await message_bus.subscribe_connection_to_execution(
            "test-conn-001", "test-exec-001"
        )
        print("✓ Subscribed to execution")
        
        # Broadcast message
        test_message = {"type": "test", "data": "hello"}
        await message_bus.broadcast_to_execution("test-exec-001", test_message)
        
        # Give time for async delivery
        await asyncio.sleep(0.1)
        
        if received_messages:
            print(f"✓ Received {len(received_messages)} messages")
        
        # Test event bus
        from dipeo.domain.events.contracts import ExecutionStartedEvent as ExecutionStarted
        from datetime import datetime
        import uuid
        
        received_events = []
        
        async def event_handler(event):
            received_events.append(event)
        
        await event_bus.subscribe(ExecutionStarted, event_handler)
        
        # Publish event
        event = ExecutionStarted(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            aggregate_id="test-exec-001",
            diagram_id="test-diagram-001",
            variables={},
        )
        await event_bus.publish(event)
        
        await asyncio.sleep(0.1)
        
        if received_events:
            print(f"✓ Received {len(received_events)} domain events")
        
        # Cleanup
        await message_bus.cleanup()
        await event_bus.cleanup()
        
        return True
        
    except Exception as e:
        print(f"✗ Messaging adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_adapters(registry: ServiceRegistry) -> bool:
    """Test LLM adapters."""
    print("\n=== Testing LLM Adapters ===")
    
    try:
        # Get services
        llm_client = registry.resolve(LLM_CLIENT)
        llm_service = registry.resolve(LLM_SERVICE)
        
        # Initialize if needed
        if hasattr(llm_client, 'initialize'):
            await llm_client.initialize()
        
        print("✓ LLM adapters initialized")
        
        # Test token counting
        usage = {"input_tokens": 100, "output_tokens": 50}
        token_usage = llm_client.get_token_counts("openai", usage)
        assert token_usage.input == 100
        assert token_usage.output == 50
        print("✓ Token counting works")
        
        # Test provider detection
        provider = await llm_service.get_provider_for_model("gpt-5-nano-2025-08-07")
        assert provider == "openai"
        print(f"✓ Provider detection: {provider}")
        
        return True
        
    except Exception as e:
        print(f"✗ LLM adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_adapters(registry: ServiceRegistry) -> bool:
    """Test API adapters."""
    print("\n=== Testing API Adapters ===")
    
    try:
        # Get services
        provider_registry = registry.resolve(API_PROVIDER_REGISTRY)
        api_invoker = registry.resolve(API_INVOKER)
        
        # Initialize if needed
        if hasattr(provider_registry, 'initialize'):
            await provider_registry.initialize()
        
        # List providers
        providers = provider_registry.list_providers()
        print(f"✓ Found {len(providers)} providers: {providers}")
        
        # Get provider manifest
        if providers:
            manifest = provider_registry.get_provider_manifest(providers[0])
            if manifest:
                print(f"✓ Got manifest for {providers[0]}")
        
        # Test validation
        is_valid = await api_invoker.validate_operation("test", "echo", {"data": "test"})
        print(f"✓ Operation validation: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"✗ API adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("Wave 2 Adapter Tests")
    print("=" * 50)
    
    # Show feature flag status
    flags = get_feature_flag_status()
    print("\nFeature Flags:")
    for service, enabled in flags.items():
        status = "✓" if enabled else "✗"
        print(f"  {status} {service}: {'V2' if enabled else 'V1'}")
    
    # Enable V2 for testing
    os.environ["DIPEO_PORT_V2"] = "1"
    print("\nEnabling V2 ports for testing...")
    
    # Create registry and wire services
    registry = ServiceRegistry()
    wire_all_v2_services(registry)
    
    # Run tests
    results = []
    
    results.append(await test_state_adapters(registry))
    results.append(await test_messaging_adapters(registry))
    results.append(await test_llm_adapters(registry))
    results.append(await test_api_adapters(registry))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  Passed: {sum(results)}/{len(results)}")
    print(f"  Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)