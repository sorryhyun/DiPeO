import asyncio
import time
from datetime import datetime
from typing import Any

from ..api_client import DiPeoAPIClient
from ..execution_options import ExecutionMode, ExecutionOptions


class ServerDiagramRunner:
    """Handles diagram execution via GraphQL API"""

    def __init__(self, options: ExecutionOptions):
        self.options = options
        self.node_timings = {} if options.debug else None
        self.last_activity_time = time.time()

    async def execute(
        self, diagram: dict[str, Any], host: str = "localhost:8000"
    ) -> dict[str, Any]:
        """Execute diagram via GraphQL"""
        result = {
            "context": {},
            "total_token_count": 0,
            "messages": [],
            "execution_id": None,
        }

        async with DiPeoAPIClient(host=host) as client:
            try:
                # For CLI, we can execute diagrams directly without saving
                if self.options.debug:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[🕰️ {timestamp}] 🐛 Debug: Executing diagram directly...")

                # Execute the diagram directly with diagram_data
                execution_id = await client.execute_diagram(
                    diagram_data=diagram,
                    debug_mode=self.options.debug,
                    timeout=self.options.timeout,
                )

                result["execution_id"] = execution_id

                if self.options.debug:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(
                        f"[🕰️ {timestamp}] 🚀 Execution started with ID: {execution_id}"
                    )
                    if self.options.mode == ExecutionMode.MONITOR:
                        print(
                            f"[🕰️ {timestamp}] 📊 Monitor mode active - server will keep running"
                        )

                # Subscribe to updates
                await self._handle_execution_streams(client, execution_id, result)

                if not result.get("error"):
                    print("\n✨ Execution completed successfully!")

            except Exception as e:
                if self.options.debug:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[🕰️ {timestamp}] ❌ Error during execution: {e!s}")
                result["error"] = str(e)

        return result

    async def _handle_execution_streams(
        self, client: DiPeoAPIClient, execution_id: str, result: dict[str, Any]
    ):
        """Handle all execution update streams"""
        # Create concurrent tasks for different streams
        node_task = asyncio.create_task(
            self._handle_node_stream(client, execution_id, result)
        )
        prompt_task = asyncio.create_task(
            self._handle_prompt_stream(client, execution_id)
        )
        exec_task = asyncio.create_task(
            self._handle_execution_stream(client, execution_id, result)
        )

        # Wait for execution to complete - exec_task should determine when we're done
        try:
            # Run all tasks concurrently but wait for exec_task to complete
            exec_result = await exec_task
            
            # Once execution is done, cancel other tasks
            node_task.cancel()
            prompt_task.cancel()
            
            # Wait for cancellation to complete
            await asyncio.gather(node_task, prompt_task, return_exceptions=True)
            
            # Update result with execution data
            if exec_result and "error" in exec_result:
                result["error"] = exec_result["error"]
            else:
                result.update(exec_result or {})
                
        except Exception as e:
            # Cancel all tasks on error
            node_task.cancel()
            prompt_task.cancel()
            exec_task.cancel()
            await asyncio.gather(node_task, prompt_task, exec_task, return_exceptions=True)
            raise

    async def _handle_node_stream(
        self, client: DiPeoAPIClient, execution_id: str, result: dict[str, Any]
    ) -> None:
        """Handle node update stream"""
        try:
            async for update in client.subscribe_to_node_updates(execution_id):
                self.last_activity_time = time.time()

                node_id = update.get("nodeId", "unknown")
                status = update.get("status", "")

                if status == "pending":
                    print(f"\n🔄 Executing node: {node_id}")
                    if self.options.debug:
                        self.node_timings[node_id] = {"start": time.time()}
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"   [🕰️ {timestamp}] Node started")

                elif status == "completed":
                    print(f"✅ Node {node_id} completed")

                    if self.options.debug and node_id in self.node_timings:
                        self.node_timings[node_id]["end"] = time.time()
                        duration = (
                            self.node_timings[node_id]["end"]
                            - self.node_timings[node_id]["start"]
                        )
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"   [🕰️ {timestamp}] Duration: {duration:.2f}s")

                    # Accumulate token count
                    # The GraphQL subscription returns 'tokens_used' field
                    tokens_used = update.get("tokens_used", 0)
                    if tokens_used:
                        result["total_token_count"] += tokens_used

                elif status == "failed":
                    error = update.get("error", "Unknown error")
                    print(f"❌ Node {node_id} failed: {error}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.options.debug:
                print(f"Error in node stream: {e}")

    async def _handle_prompt_stream(
        self, client: DiPeoAPIClient, execution_id: str
    ) -> None:
        """Handle interactive prompt stream"""
        try:
            async for prompt in client.subscribe_to_interactive_prompts(execution_id):
                # Skip None values (used when no prompts are available)
                if prompt is None:
                    continue

                node_id = prompt.get("node_id")
                prompt_text = prompt.get("prompt", "Input required:")

                print(f"\n💬 {prompt_text}")
                user_input = input("Your response: ")

                await client.submit_interactive_response(
                    execution_id, node_id, user_input
                )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Ignore subscription errors - interactive prompts are optional
            if (
                self.options.debug
                and "Subscription field must return AsyncIterable" not in str(e)
            ):
                print(f"Error in prompt stream: {e}")

    async def _handle_execution_stream(
        self, client: DiPeoAPIClient, execution_id: str, result: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle execution state stream"""
        try:
            async for update in client.subscribe_to_execution(execution_id):
                self.last_activity_time = time.time()
                status = update.get("status", "").upper()
                
                if self.options.debug:
                    print(f"🐛 Debug: Execution status update: {status}")

                if status == "COMPLETED":
                    # Try different field names for token usage
                    token_usage = update.get("tokenUsage") or update.get("token_usage") or {}
                    if self.options.debug:
                        print(f"\n🐛 Debug: Execution completed update: {update}")
                        print(f"🐛 Debug: Token usage extracted: {token_usage}")
                    return {
                        "context": update.get("nodeOutputs", {}),
                        "total_token_count": token_usage.get("total", 0)
                        if token_usage
                        else 0,
                    }

                if status in ["FAILED", "ABORTED"]:
                    return {"error": update.get("error", "Execution failed")}

                # Check timeout
                elapsed = time.time() - self.last_activity_time
                if elapsed > self.options.timeout:
                    print(
                        f"\n⏱️  Timeout: No execution activity for {self.options.timeout} seconds"
                    )
                    await client.control_execution(execution_id, "abort")
                    return {
                        "error": f"Execution timeout after {self.options.timeout} seconds"
                    }

        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.options.debug:
                print(f"Error in execution stream: {e}")
            import traceback

            traceback.print_exc()
            return {"error": str(e)}

        return {}
