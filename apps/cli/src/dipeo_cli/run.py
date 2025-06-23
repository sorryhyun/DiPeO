"""
Run command implementation for DiPeO CLI.

This module handles diagram execution through the GraphQL API.
"""

import asyncio
import json
import os
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .api_client import DiPeoAPIClient
from .utils import DiagramLoader, DiagramConverter


class ExecutionMode(Enum):
    """Execution modes for diagram runs"""

    STANDARD = "standard"
    MONITOR = "monitor"
    HEADLESS = "headless"
    CHECK = "check"


@dataclass
class ExecutionOptions:
    """Configuration for diagram execution"""

    mode: ExecutionMode = ExecutionMode.STANDARD
    show_browser: bool = True
    pre_initialize: bool = True
    stream: bool = True
    debug: bool = False
    timeout: int = 300  # 5 minutes
    output_file: Optional[str] = None
    diagram_file: Optional[str] = None


class DiagramRunner:
    """Handles diagram execution via GraphQL API"""

    def __init__(self, options: ExecutionOptions):
        self.options = options
        self.node_timings = {} if options.debug else None
        self.last_activity_time = time.time()

    async def execute(
        self, diagram: Dict[str, Any], host: str = "localhost:8000"
    ) -> Dict[str, Any]:
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
                    print("🐛 Debug: Executing diagram directly...")

                # Execute the diagram directly with diagram_data
                execution_id = await client.execute_diagram(
                    diagram_data=diagram,
                    debug_mode=self.options.debug,
                    timeout=self.options.timeout,
                )

                result["execution_id"] = execution_id

                if self.options.debug:
                    print(f"🚀 Execution started with ID: {execution_id}")

                # Subscribe to updates
                await self._handle_execution_streams(client, execution_id, result)

                if self.options.stream and not result.get("error"):
                    print("\n✨ Execution completed successfully!")

            except Exception as e:
                if self.options.debug:
                    print(f"❌ Error during execution: {e!s}")
                result["error"] = str(e)

        return result

    async def _handle_execution_streams(
        self, client: DiPeoAPIClient, execution_id: str, result: Dict[str, Any]
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

        # Wait for execution to complete
        tasks = [node_task, prompt_task, exec_task]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Check if execution completed successfully
        if exec_task in done:
            exec_result = await exec_task
            if exec_result and "error" in exec_result:
                result["error"] = exec_result["error"]
            else:
                result.update(exec_result or {})

    async def _handle_node_stream(
        self, client: DiPeoAPIClient, execution_id: str, result: Dict[str, Any]
    ) -> None:
        """Handle node update stream"""
        try:
            async for update in client.subscribe_to_node_updates(execution_id):
                self.last_activity_time = time.time()

                node_id = update.get("nodeId", "unknown")
                status = update.get("status", "")

                if status == "started" and self.options.stream:
                    print(f"\n🔄 Executing node: {node_id}")
                    if self.options.debug:
                        self.node_timings[node_id] = {"start": time.time()}

                elif status == "completed":
                    if self.options.stream:
                        print(f"✅ Node {node_id} completed")

                    if self.options.debug and node_id in self.node_timings:
                        self.node_timings[node_id]["end"] = time.time()
                        duration = (
                            self.node_timings[node_id]["end"]
                            - self.node_timings[node_id]["start"]
                        )
                        print(f"   Duration: {duration:.2f}s")

                    # Accumulate token count
                    tokens_used = update.get("tokensUsed", 0)
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
                    
                node_id = prompt.get("nodeId")
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
            if self.options.debug and "Subscription field must return AsyncIterable" not in str(e):
                print(f"Error in prompt stream: {e}")

    async def _handle_execution_stream(
        self, client: DiPeoAPIClient, execution_id: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle execution state stream"""
        try:
            async for update in client.subscribe_to_execution(execution_id):
                self.last_activity_time = time.time()

                status = update.get("status", "").upper()

                if status == "COMPLETED":
                    # Extract final results
                    token_usage = update.get("tokenUsage", {})
                    return {
                        "context": update.get("nodeOutputs", {}),
                        "total_token_count": token_usage.get("total", 0) if token_usage else 0,
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
            return {"error": str(e)}

        return {}


async def run_command(args: List[str]) -> None:
    """Execute run command"""
    if not args:
        print("Error: Missing input file")
        return

    file_path = args[0]
    options = _parse_run_options(args[1:])
    options.diagram_file = file_path  # Store the file path for later use

    # Restart backend server if debug mode
    if options.debug:
        await _restart_backend_server()

    # Load diagram
    diagram = DiagramLoader.load(file_path)
    
    # Convert to GraphQL format if needed
    diagram = DiagramConverter.to_graphql_format(diagram)

    # Handle special modes
    if options.mode == ExecutionMode.MONITOR:
        await _run_monitor_mode(diagram, options)
        # Don't return here - continue to execute the diagram

    # Execute diagram (both for normal and monitor mode)
    executor = DiagramRunner(options)
    result = await executor.execute(diagram)

    print(
        f"✓ Execution complete - Total token count: {result.get('total_token_count', 0)}"
    )

    # Save results
    _save_results(result, options)


def _parse_run_options(args: List[str]) -> ExecutionOptions:
    """Parse command line options for run command"""
    options = ExecutionOptions()

    for arg in args:
        if arg == "--monitor":
            options.mode = ExecutionMode.MONITOR
        elif arg == "--mode=headless":
            options.mode = ExecutionMode.HEADLESS
            options.show_browser = False
        elif arg == "--mode=check":
            options.mode = ExecutionMode.CHECK
            options.show_browser = False
        elif arg == "--no-browser":
            options.show_browser = False
        elif arg == "--no-preload":
            options.pre_initialize = False
        elif arg == "--no-stream":
            options.stream = False
        elif arg == "--debug":
            options.debug = True
        elif arg.startswith("--timeout="):
            try:
                options.timeout = int(arg.split("=")[1])
            except ValueError:
                print("Error: Invalid timeout value. Using default.")
        elif not arg.startswith("--"):
            options.output_file = arg

    return options


async def _run_monitor_mode(diagram: Dict[str, Any], options: ExecutionOptions) -> None:
    """Handle monitor mode setup"""
    import webbrowser
    from pathlib import Path
    
    # Extract diagram ID from file path (e.g., quicksave.json -> quicksave)
    if options.diagram_file:
        diagram_id = Path(options.diagram_file).stem
    else:
        # Fallback to metadata name or "unknown"
        diagram_id = diagram.get("metadata", {}).get("name", "unknown")
    
    # Open browser with both monitor mode and diagram ID
    monitor_url = f"http://localhost:3000/?monitor=true&diagram={diagram_id}"
    webbrowser.open(monitor_url)
    
    # Wait for browser to load
    await asyncio.sleep(2.0)
    print(f"✓ Monitor ready - Diagram: {diagram_id}")


async def _restart_backend_server() -> None:
    """Restart the backend server to ensure latest code is loaded"""
    print("🐛 Debug: Restarting backend server with DEBUG logging...")
    
    # Kill any existing server processes
    try:
        # Kill processes listening on port 8000
        kill_result = subprocess.run(
            ["pkill", "-f", "python main.py"],
            capture_output=True,
            text=True
        )
        
        # Also try to kill hypercorn processes
        subprocess.run(
            ["pkill", "-f", "hypercorn"],
            capture_output=True,
            text=True
        )
        
        # Give processes time to shut down
        await asyncio.sleep(1.0)
        
        print("🔄 Killed existing server processes")
    except Exception as e:
        print(f"⚠️  Could not kill existing processes: {e}")
    
    # Start new server process with DEBUG logging
    server_path = Path(__file__).parent.parent.parent.parent.parent / "apps" / "server"
    env = os.environ.copy()
    env["LOG_LEVEL"] = "DEBUG"
    
    start_cmd = ["python", "main.py"]
    
    try:
        # Start server in background with debug output visible
        process = subprocess.Popen(
            start_cmd,
            cwd=server_path,
            env=env,
            stdout=None,  # Show output in terminal
            stderr=None,  # Show errors in terminal
            start_new_session=True
        )
        
        print("⏳ Waiting for server to start...")
        
        # Wait for server to be ready
        max_attempts = 20  # 10 seconds timeout
        for i in range(max_attempts):
            try:
                async with DiPeoAPIClient("localhost:8000") as client:
                    # Try to connect with a simple query
                    query = """
                        query {
                            __typename
                        }
                    """
                    await client._execute_query(query)
                    break
            except Exception:
                if i == max_attempts - 1:
                    print("❌ Failed to start backend server")
                    raise
                await asyncio.sleep(0.5)
        
        print("✅ Backend server started with DEBUG logging")
        print("📋 You should see [DEBUG] messages in the server output\n")
        
    except Exception as e:
        print(f"❌ Error starting backend server: {e}")
        print("Please start the server manually with: cd apps/server && LOG_LEVEL=DEBUG python main.py")
        raise


def _save_results(result: Dict[str, Any], options: ExecutionOptions) -> None:
    """Save execution results"""
    Path("files/results").mkdir(parents=True, exist_ok=True)
    save_path = options.output_file or "files/results/results.json"

    with open(save_path, "w") as f:
        json.dump(result, f, indent=2)

    if options.debug:
        print(f"  Results saved to: {save_path}")
