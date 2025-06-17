"""
Run command implementation for DiPeO CLI.

This module handles diagram execution through the GraphQL API.
"""

import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List

from .api_client import DiPeoAPIClient
from .utils import DiagramLoader


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


class DiagramExecutor:
    """Handles diagram execution via GraphQL API"""
    
    def __init__(self, options: ExecutionOptions):
        self.options = options
        self.node_timings = {} if options.debug else None
        self.last_activity_time = time.time()
    
    async def execute(self, diagram: Dict[str, Any], host: str = "localhost:8000") -> Dict[str, Any]:
        """Execute diagram via GraphQL"""
        result = {
            "context": {},
            "total_token_count": 0,
            "messages": [],
            "execution_id": None
        }
        
        async with DiPeoAPIClient(host=host) as client:
            try:
                # Save the diagram first to get a diagram_id
                if self.options.debug:
                    print("🐛 Debug: Saving diagram to server...")
                
                diagram_id = await client.save_diagram(diagram)
                
                if self.options.debug:
                    print(f"🐛 Debug: Diagram saved with ID: {diagram_id}")
                
                # Execute the saved diagram
                execution_id = await client.execute_diagram(
                    diagram_id=diagram_id,
                    debug_mode=self.options.debug,
                    timeout=self.options.timeout
                )
                
                result['execution_id'] = execution_id
                
                if self.options.debug:
                    print(f"🚀 Execution started with ID: {execution_id}")
                
                # Subscribe to updates
                await self._handle_execution_streams(client, execution_id, result)
                
                if self.options.stream and not result.get('error'):
                    print("\n✨ Execution completed successfully!")
                    
            except Exception as e:
                if self.options.debug:
                    print(f"❌ Error during execution: {str(e)}")
                result['error'] = str(e)
        
        return result
    
    async def _handle_execution_streams(self, client: DiPeoAPIClient, execution_id: str, result: Dict[str, Any]):
        """Handle all execution update streams"""
        # Create concurrent tasks for different streams
        node_task = asyncio.create_task(self._handle_node_stream(client, execution_id, result))
        prompt_task = asyncio.create_task(self._handle_prompt_stream(client, execution_id))
        exec_task = asyncio.create_task(self._handle_execution_stream(client, execution_id, result))
        
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
            if exec_result and 'error' in exec_result:
                result['error'] = exec_result['error']
            else:
                result.update(exec_result or {})
    
    async def _handle_node_stream(self, client: DiPeoAPIClient, execution_id: str, result: Dict[str, Any]) -> None:
        """Handle node update stream"""
        try:
            async for update in client.subscribe_to_node_updates(execution_id):
                self.last_activity_time = time.time()
                
                node_id = update.get('nodeId', 'unknown')
                status = update.get('status', '')
                
                if status == 'started' and self.options.stream:
                    print(f"\n🔄 Executing node: {node_id}")
                    if self.options.debug:
                        self.node_timings[node_id] = {'start': time.time()}
                
                elif status == 'completed':
                    if self.options.stream:
                        print(f"✅ Node {node_id} completed")
                    
                    if self.options.debug and node_id in self.node_timings:
                        self.node_timings[node_id]['end'] = time.time()
                        duration = self.node_timings[node_id]['end'] - self.node_timings[node_id]['start']
                        print(f"   Duration: {duration:.2f}s")
                    
                    # Accumulate token count
                    tokens_used = update.get('tokensUsed', 0)
                    if tokens_used:
                        result['total_token_count'] += tokens_used
                
                elif status == 'failed':
                    error = update.get('error', 'Unknown error')
                    print(f"❌ Node {node_id} failed: {error}")
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.options.debug:
                print(f"Error in node stream: {e}")
    
    async def _handle_prompt_stream(self, client: DiPeoAPIClient, execution_id: str) -> None:
        """Handle interactive prompt stream"""
        try:
            async for prompt in client.subscribe_to_interactive_prompts(execution_id):
                node_id = prompt.get('nodeId')
                prompt_text = prompt.get('prompt', 'Input required:')
                
                print(f"\n💬 {prompt_text}")
                user_input = input("Your response: ")
                
                await client.submit_interactive_response(execution_id, node_id, user_input)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.options.debug:
                print(f"Error in prompt stream: {e}")
    
    async def _handle_execution_stream(self, client: DiPeoAPIClient, execution_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execution state stream"""
        try:
            async for update in client.subscribe_to_execution(execution_id):
                self.last_activity_time = time.time()
                
                status = update.get('status', '').upper()
                
                if status == 'COMPLETED':
                    # Extract final results
                    return {
                        'context': update.get('nodeOutputs', {}),
                        'total_token_count': update.get('totalTokens', 0)
                    }
                
                elif status in ['FAILED', 'ABORTED']:
                    return {'error': update.get('error', 'Execution failed')}
                
                # Check timeout
                elapsed = time.time() - self.last_activity_time
                if elapsed > self.options.timeout:
                    print(f"\n⏱️  Timeout: No execution activity for {self.options.timeout} seconds")
                    await client.control_execution(execution_id, 'abort')
                    return {'error': f"Execution timeout after {self.options.timeout} seconds"}
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.options.debug:
                print(f"Error in execution stream: {e}")
            return {'error': str(e)}
        
        return {}


async def run_command(args: List[str]) -> None:
    """Execute run command"""
    if not args:
        print("Error: Missing input file")
        return
    
    file_path = args[0]
    options = _parse_run_options(args[1:])
    
    # Load diagram
    diagram = DiagramLoader.load(file_path)
    
    # Handle special modes
    if options.mode == ExecutionMode.MONITOR:
        await _run_monitor_mode(diagram, options)
    
    # Execute diagram
    executor = DiagramExecutor(options)
    result = await executor.execute(diagram)
    
    print(f"✓ Execution complete - Total token count: {result.get('total_token_count', 0)}")
    
    # Save results
    _save_results(result, options)


def _parse_run_options(args: List[str]) -> ExecutionOptions:
    """Parse command line options for run command"""
    options = ExecutionOptions()
    
    for arg in args:
        if arg == '--monitor':
            options.mode = ExecutionMode.MONITOR
        elif arg == '--mode=headless':
            options.mode = ExecutionMode.HEADLESS
            options.show_browser = False
        elif arg == '--mode=check':
            options.mode = ExecutionMode.CHECK
            options.show_browser = False
        elif arg == '--no-browser':
            options.show_browser = False
        elif arg == '--no-preload':
            options.pre_initialize = False
        elif arg == '--no-stream':
            options.stream = False
        elif arg == '--debug':
            options.debug = True
        elif arg.startswith('--timeout='):
            try:
                options.timeout = int(arg.split('=')[1])
            except ValueError:
                print("Error: Invalid timeout value. Using default.")
        elif not arg.startswith('--'):
            options.output_file = arg
    
    return options


async def _run_monitor_mode(diagram: Dict[str, Any], options: ExecutionOptions) -> None:
    """Handle monitor mode setup"""
    import webbrowser
    
    # Open browser
    monitor_url = "http://localhost:3000/?monitor=true"
    webbrowser.open(monitor_url)
    
    # Wait for browser to load
    await asyncio.sleep(2.0)
    print("✓ Monitor ready")
    
    # Note: Browser will connect directly to GraphQL for monitoring


def _save_results(result: Dict[str, Any], options: ExecutionOptions) -> None:
    """Save execution results"""
    Path('files/results').mkdir(parents=True, exist_ok=True)
    save_path = options.output_file or 'files/results/results.json'
    
    with open(save_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    if options.debug:
        print(f"  Results saved to: {save_path}")