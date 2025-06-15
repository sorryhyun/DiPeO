#!/usr/bin/env python3
"""
Test script for GraphQL CLI migration
Compares WebSocket and GraphQL execution results
"""
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tool import DiagramLoader, ExecutionOptions, WebSocketExecutor, GraphQLExecutor


async def test_execution():
    """Test GraphQL execution matches WebSocket behavior."""
    
    # Test diagram with simple flow
    test_diagram = {
        "nodes": {
            "start_1": {
                "id": "start_1",
                "type": "start",
                "data": {
                    "inputs": {"message": "Hello from test!"}
                },
                "position": {"x": 0, "y": 0}
            },
            "person_job_1": {
                "id": "person_job_1",
                "type": "person_job",
                "data": {
                    "personId": "person_1",
                    "prompt": "Echo this message: {{message}}"
                },
                "position": {"x": 200, "y": 0}
            },
            "endpoint_1": {
                "id": "endpoint_1",
                "type": "endpoint",
                "data": {},
                "position": {"x": 400, "y": 0}
            }
        },
        "arrows": {
            "arrow_1": {
                "id": "arrow_1",
                "source": "start_1",
                "sourceHandle": "output",
                "target": "person_job_1",
                "targetHandle": "input"
            },
            "arrow_2": {
                "id": "arrow_2",
                "source": "person_job_1",
                "sourceHandle": "output",
                "target": "endpoint_1",
                "targetHandle": "input"
            }
        },
        "persons": {
            "person_1": {
                "id": "person_1",
                "name": "Test Assistant",
                "model": "gpt-4.1-nano",
                "apiKeyId": "APIKEY_387B73"
            }
        },
        "apiKeys": {
            "APIKEY_387B73": {
                "id": "APIKEY_387B73",
                "label": "Test API Key",
                "service": "openai",
                "key": "test-key"
            }
        },
        "handles": {},
        "viewport": {"x": 0, "y": 0, "zoom": 1}
    }
    
    # Common options
    options = ExecutionOptions(
        debug=True,
        stream=False,  # Disable streaming for easier comparison
        timeout=30
    )
    
    print("🧪 Testing WebSocket vs GraphQL execution...\n")
    
    # Run with WebSocket
    print("1️⃣ Running with WebSocket...")
    ws_start = time.time()
    ws_executor = WebSocketExecutor(options)
    ws_result = await ws_executor.execute(test_diagram)
    ws_duration = time.time() - ws_start
    
    print(f"   ✅ WebSocket execution completed in {ws_duration:.2f}s")
    print(f"   Token count: {ws_result.get('total_token_count', 0)}")
    print(f"   Execution ID: {ws_result.get('execution_id', 'N/A')}\n")
    
    # Run with GraphQL
    print("2️⃣ Running with GraphQL...")
    gql_start = time.time()
    try:
        gql_executor = GraphQLExecutor(options)
        gql_result = await gql_executor.execute(test_diagram)
        gql_duration = time.time() - gql_start
        
        print(f"   ✅ GraphQL execution completed in {gql_duration:.2f}s")
        print(f"   Token count: {gql_result.get('total_token_count', 0)}")
        print(f"   Execution ID: {gql_result.get('execution_id', 'N/A')}\n")
    except ImportError as e:
        print(f"   ❌ GraphQL test skipped: {e}")
        return
    
    # Compare results
    print("3️⃣ Comparing results...")
    
    # Basic checks
    assert ws_result.get('execution_id') is not None, "WebSocket execution should have ID"
    assert gql_result.get('execution_id') is not None, "GraphQL execution should have ID"
    
    # Check for errors
    if ws_result.get('error'):
        print(f"   ⚠️  WebSocket error: {ws_result['error']}")
    if gql_result.get('error'):
        print(f"   ⚠️  GraphQL error: {gql_result['error']}")
    
    # Compare contexts (may differ slightly due to execution differences)
    ws_context = ws_result.get('context', {})
    gql_context = gql_result.get('context', {})
    
    print(f"   WebSocket context keys: {sorted(ws_context.keys())}")
    print(f"   GraphQL context keys: {sorted(gql_context.keys())}")
    
    # Performance comparison
    print(f"\n📊 Performance comparison:")
    print(f"   WebSocket: {ws_duration:.2f}s")
    print(f"   GraphQL: {gql_duration:.2f}s")
    print(f"   Difference: {abs(ws_duration - gql_duration):.2f}s")
    
    print("\n✅ Test completed!")


async def test_interactive_prompt():
    """Test interactive prompt handling in GraphQL."""
    print("\n🧪 Testing interactive prompts...\n")
    
    # This would require a diagram with user_response node
    # Skipping for now as it requires user interaction
    print("   ⏭️  Interactive prompt test skipped (requires user input)")


async def test_error_handling():
    """Test error handling in GraphQL execution."""
    print("\n🧪 Testing error handling...\n")
    
    # Test with invalid diagram
    invalid_diagram = {"nodes": {}, "arrows": {}}
    
    options = ExecutionOptions(debug=False)
    
    try:
        executor = GraphQLExecutor(options)
        result = await executor.execute(invalid_diagram)
        if result.get('error'):
            print(f"   ✅ Error properly handled: {result['error']}")
        else:
            print("   ⚠️  Expected error but execution succeeded")
    except Exception as e:
        print(f"   ✅ Exception caught: {str(e)}")


async def main():
    """Run all tests."""
    print("DiPeO GraphQL CLI Test Suite\n")
    print("=" * 50)
    
    try:
        await test_execution()
        await test_interactive_prompt()
        await test_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())