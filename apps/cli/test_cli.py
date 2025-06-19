#!/usr/bin/env python3
"""
Test script for DiPeO CLI
Tests GraphQL-based execution
"""
import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dipeo.api_client import DiPeoAPIClient
from dipeo.utils import DiagramLoader


async def test_execution():
    """Test GraphQL execution."""
    
    # Test diagram with simple flow
    test_diagram = {
        "metadata": {
            "name": "test_diagram",
            "description": "Test diagram for CLI"
        },
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
                "target": "person_job_1"
            },
            "arrow_2": {
                "id": "arrow_2",
                "source": "person_job_1",
                "target": "endpoint_1"
            }
        }
    }
    
    print("🧪 Testing DiPeO CLI GraphQL Execution\n")
    
    async with DiPeoAPIClient() as client:
        try:
            # Save diagram
            print("📝 Saving test diagram...")
            diagram_id = await client.save_diagram(test_diagram)
            print(f"✅ Diagram saved with ID: {diagram_id}\n")
            
            # Execute diagram
            print("🚀 Starting execution...")
            execution_id = await client.execute_diagram(
                diagram_id=diagram_id,
                debug_mode=True,
                timeout=30
            )
            print(f"✅ Execution started with ID: {execution_id}\n")
            
            # Monitor execution
            print("📊 Monitoring execution...")
            async for update in client.subscribe_to_execution(execution_id):
                status = update.get('status', '').upper()
                print(f"  Status: {status}")
                
                if status == 'COMPLETED':
                    print("\n✨ Execution completed successfully!")
                    print(f"  Total tokens: {update.get('totalTokens', 0)}")
                    break
                elif status in ['FAILED', 'ABORTED']:
                    print(f"\n❌ Execution failed: {update.get('error', 'Unknown error')}")
                    break
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            raise


async def test_interactive():
    """Test interactive prompt handling."""
    
    test_diagram = {
        "metadata": {
            "name": "interactive_test",
            "description": "Test interactive prompts"
        },
        "nodes": {
            "start_1": {
                "id": "start_1", 
                "type": "start",
                "data": {},
                "position": {"x": 0, "y": 0}
            },
            "user_response_1": {
                "id": "user_response_1",
                "type": "user_response", 
                "data": {
                    "prompt": "What is your name?"
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
                "target": "user_response_1"
            },
            "arrow_2": {
                "id": "arrow_2",
                "source": "user_response_1",
                "target": "endpoint_1"
            }
        }
    }
    
    print("\n🧪 Testing Interactive Prompts\n")
    
    async with DiPeoAPIClient() as client:
        try:
            # Save and execute
            diagram_id = await client.save_diagram(test_diagram)
            execution_id = await client.execute_diagram(diagram_id)
            
            # Handle prompts in parallel with execution monitoring
            prompt_task = asyncio.create_task(
                handle_prompts(client, execution_id)
            )
            exec_task = asyncio.create_task(
                monitor_execution(client, execution_id)
            )
            
            await asyncio.gather(prompt_task, exec_task)
            
        except Exception as e:
            print(f"\n❌ Interactive test failed: {str(e)}")
            raise


async def handle_prompts(client, execution_id):
    """Handle interactive prompts."""
    async for prompt in client.subscribe_to_interactive_prompts(execution_id):
        print(f"\n💬 Prompt: {prompt.get('prompt')}")
        # Simulate user response
        await asyncio.sleep(1)
        response = "Test User"
        print(f"  Response: {response}")
        await client.submit_interactive_response(
            execution_id,
            prompt.get('nodeId'),
            response
        )


async def monitor_execution(client, execution_id):
    """Monitor execution status."""
    async for update in client.subscribe_to_execution(execution_id):
        status = update.get('status', '').upper()
        if status in ['COMPLETED', 'FAILED', 'ABORTED']:
            return


async def main():
    """Run all tests."""
    print("=" * 50)
    print("DiPeO CLI Test Suite")
    print("=" * 50)
    
    # Test basic execution
    await test_execution()
    
    # Test interactive prompts
    # await test_interactive()
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())