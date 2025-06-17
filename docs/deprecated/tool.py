#!/usr/bin/env python3
"""
DiPeO CLI Tool - Refactored Version
A streamlined command-line interface for DiPeO diagram operations
"""

import json
import sys
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime

import yaml
# import websockets  # Deprecated - using GraphQL subscriptions
import requests
import os


# Constants
API_URL = "http://localhost:8000"
# WS_URL = "ws://localhost:8000/api/ws"  # Deprecated - WebSocket endpoint removed
GRAPHQL_HOST = "localhost:8000"  # GraphQL endpoint on main server
DEFAULT_API_KEY = "APIKEY_387B73"
DEFAULT_TIMEOUT = 300  # 5 minutes
DEFAULT_MODEL = "gpt-4.1-nano"


class ExecutionMode(Enum):
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
    timeout: int = DEFAULT_TIMEOUT
    output_file: Optional[str] = None


# Import from the new CLI package
try:
    from cli.dipeo_cli.utils import DiagramValidator
except ImportError:
    # Fallback for backward compatibility
    class DiagramValidator:
        """Basic diagram validator fallback"""
        @staticmethod
        def validate_diagram(diagram: Dict[str, Any]) -> Dict[str, Any]:
            """Basic validation without models"""
            # Ensure all required fields exist
            if 'nodes' not in diagram:
                diagram['nodes'] = {}
            if 'arrows' not in diagram:
                diagram['arrows'] = {}
            if 'handles' not in diagram:
                diagram['handles'] = {}
            if 'persons' not in diagram:
                diagram['persons'] = {}
            if 'apiKeys' not in diagram:
                diagram['apiKeys'] = {}
            
            # Add default API key if needed
            if not diagram['apiKeys'] and diagram['persons']:
                diagram['apiKeys'][DEFAULT_API_KEY] = {
                    'id': DEFAULT_API_KEY,
                    'label': 'Default API Key',
                    'service': 'openai',
                    'key': 'test-key'
                }
            
            # Add metadata if missing
            if 'metadata' not in diagram:
                diagram['metadata'] = {
                    'name': 'CLI Diagram',
                    'created': datetime.now().isoformat(),
                    'modified': datetime.now().isoformat(),
                    'version': '2.0.0'
                }
            
            return diagram


class DiagramLoader:
    """Handles loading and saving diagrams"""
    
    @staticmethod
    def load(file_path: str) -> Dict[str, Any]:
        """Load diagram from JSON or YAML file"""
        path = Path(file_path)
        
        with open(file_path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                diagram = yaml.safe_load(f)
            else:
                diagram = json.load(f)
        
        return DiagramValidator.validate_diagram(diagram)
    
    @staticmethod
    def save(diagram: Dict[str, Any], file_path: str) -> None:
        """Save diagram to JSON or YAML file"""
        path = Path(file_path)
        
        with open(file_path, 'w') as f:
            if path.suffix in ['.yaml', '.yml']:
                yaml.dump(diagram, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(diagram, f, indent=2)


class WebSocketExecutor:
    """DEPRECATED: WebSocket support has been removed in favor of GraphQL subscriptions"""
    
    def __init__(self, options: ExecutionOptions):
        self.options = options
        self.node_timings = {} if options.debug else None
        self.last_activity_time = time.time()
    
    async def execute(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute diagram via WebSocket (DEPRECATED)"""
        result = {
            "context": {},
            "total_token_count": 0,
            "messages": [],
            "execution_id": None,
            "error": "WebSocket endpoint has been deprecated. Please use GraphQL (default) instead."
        }
        
        print("❌ Error: WebSocket endpoint '/api/ws' has been removed.")
        print("✨ GraphQL is now the default execution mode with real-time subscriptions.")
        print("💡 Remove the '--use-websocket' flag to use GraphQL.")
        
        return result


class GraphQLExecutor:
    """Handles GraphQL-based diagram execution"""
    
    def __init__(self, options: ExecutionOptions):
        self.options = options
        self.node_timings = {} if options.debug else None
        self.last_activity_time = time.time()
    
    async def execute(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute diagram via GraphQL"""
        try:
            from cli.dipeo_cli.api_client import DiPeoAPIClient as DiPeoGraphQLClient
        except ImportError:
            print("❌ GraphQL dependencies not installed. Run: pip install -r requirements-cli.txt")
            sys.exit(1)
        
        result = {
            "context": {},
            "total_token_count": 0,
            "messages": [],
            "execution_id": None
        }
        
        async with DiPeoGraphQLClient(host=GRAPHQL_HOST) as client:
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
                
                # Subscribe to node updates and interactive prompts concurrently
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
                
                if self.options.stream and not result.get('error'):
                    print("\n✨ Execution completed successfully!")
                    
            except Exception as e:
                if self.options.debug:
                    print(f"❌ Error during execution: {str(e)}")
                result['error'] = str(e)
        
        return result
    
    async def _handle_node_stream(self, client, execution_id: str, result: Dict[str, Any]) -> None:
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
    
    async def _handle_prompt_stream(self, client, execution_id: str) -> None:
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
    
    async def _handle_execution_stream(self, client, execution_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
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
    


class DiagramRunner:
    """Main diagram execution orchestrator"""
    
    def __init__(self, options: ExecutionOptions, use_websocket: bool = False):
        self.options = options
        # Use WebSocket only if explicitly requested
        if use_websocket or os.environ.get('DIPEO_USE_WEBSOCKET'):
            self.executor = WebSocketExecutor(options)
            if options.debug:
                print("🐛 Debug: Using WebSocket executor (deprecated)")
        else:
            self.executor = GraphQLExecutor(options)
            if options.debug:
                print("🐛 Debug: Using GraphQL executor")
    
    async def run(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Run diagram with specified options"""
        start_time = time.time() if self.options.debug else None
        
        if self.options.debug:
            print("🐛 Debug mode enabled - verbose output and timing information")
        
        # Handle monitor mode
        if self.options.mode == ExecutionMode.MONITOR:
            await self._run_monitor_mode(diagram)
        
        # Broadcast to browser if enabled
        if self.options.show_browser:
            await self._broadcast_to_browser(diagram)
        
        # Execute diagram
        result = await self.executor.execute(diagram)
        
        # Debug summary
        if self.options.debug and start_time:
            elapsed = time.time() - start_time
            print(f"\n🐛 Debug: Total execution time: {elapsed:.2f}s")
        
        return result
    
    async def _run_monitor_mode(self, diagram: Dict[str, Any]) -> None:
        """Handle monitor mode setup"""
        import webbrowser
        
        # Open browser
        monitor_url = "http://localhost:3000/?monitor=true"
        webbrowser.open(monitor_url)
        
        # Wait for browser to load
        await asyncio.sleep(2.0)
        print("✓ Monitor ready")
        
        # Broadcast diagram
        execution_id = f"cli_{uuid.uuid4().hex[:8]}"
        await self._broadcast_to_browser(diagram, execution_id)
        await asyncio.sleep(1.0)
    
    async def _broadcast_to_browser(self, diagram: Dict[str, Any], execution_id: Optional[str] = None) -> None:
        """Broadcast diagram to browser monitors"""
        if self.options.debug:
            print("🌐 Browser visualization enabled - open http://localhost:3000 to see execution")
        
        # Note: Browser monitoring is now handled through GraphQL subscriptions
        # The frontend connects directly to GraphQL and subscribes to execution updates
        # No separate broadcast mechanism is needed


class CommandHandler:
    """Handles CLI commands"""
    
    @staticmethod
    async def run(args: List[str]) -> None:
        """Execute run command"""
        if not args:
            print("Error: Missing input file")
            sys.exit(1)
        
        file_path = args[0]
        options, use_websocket = CommandHandler._parse_run_options(args[1:])
        
        # Load diagram
        diagram = DiagramLoader.load(file_path)
        
        # Run diagram
        runner = DiagramRunner(options, use_websocket=use_websocket)
        result = await runner.run(diagram)
        
        print(f"✓ Execution complete - Total token count: {result.get('total_token_count', 0)}")
        
        # Save results
        CommandHandler._save_results(result, options)
    
    @staticmethod
    def _parse_run_options(args: List[str]) -> tuple[ExecutionOptions, bool]:
        """Parse command line options for run command"""
        options = ExecutionOptions()
        use_websocket = False
        
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
            elif arg == '--use-websocket':
                use_websocket = True
            elif arg.startswith('--timeout='):
                try:
                    options.timeout = int(arg.split('=')[1])
                except ValueError:
                    print("Error: Invalid timeout value. Using default.")
            elif not arg.startswith('--'):
                options.output_file = arg
        
        return options, use_websocket
    
    @staticmethod
    def _save_results(result: Dict[str, Any], options: ExecutionOptions) -> None:
        """Save execution results"""
        Path('../../files/results').mkdir(parents=True, exist_ok=True)
        save_path = options.output_file or 'files/results/results.json'
        
        with open(save_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        if options.debug:
            print(f"  Results saved to: {save_path}")
    
    @staticmethod
    def convert(args: List[str]) -> None:
        """Execute convert command"""
        if len(args) < 2:
            print("Error: Usage: convert <input> <output>")
            sys.exit(1)
        
        input_path = args[0]
        output_path = args[1]
        
        # Simple conversion
        diagram = DiagramLoader.load(input_path)
        DiagramLoader.save(diagram, output_path)
        
        print(f"✓ Converted: {input_path} → {output_path}")
    
    @staticmethod
    def stats(args: List[str]) -> None:
        """Execute stats command"""
        if not args:
            print("Error: Missing input file")
            sys.exit(1)
        
        diagram = DiagramLoader.load(args[0])
        
        # Calculate statistics
        nodes = diagram.get('nodes', [])
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("\nDiagram Statistics:")
        print(f"  Persons: {len(diagram.get('persons', []))}")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Arrows: {len(diagram.get('arrows', []))}")
        print(f"  API Keys: {'Yes' if diagram.get('apiKeys') else 'No'}")
        
        if node_types:
            print("\nNode Types:")
            for node_type, count in sorted(node_types.items()):
                print(f"  {node_type}: {count}")
    
    @staticmethod
    def monitor(_: List[str]) -> None:
        """Open browser monitoring page"""
        import webbrowser
        monitor_url = "http://localhost:3000/?monitor=true"
        webbrowser.open(monitor_url)


def print_usage():
    """Print usage information"""
    print("DiPeO CLI Tool\n")
    print("Usage: python tool.py <command> [options]\n")
    print("Commands:")
    print("  run <file> [options]       - 🚀 Run diagram (uses GraphQL)")
    print("    --monitor               - Open browser monitor before execution")
    print("    --mode=headless         - Run without browser")
    print("    --no-browser            - Disable browser visualization")
    print("    --no-stream             - Disable streaming output")
    print("    --debug                 - Enable debug mode")
    print("    --timeout=<seconds>     - Set inactivity timeout (default: 300)")
    print("  monitor                    - Open browser monitoring page")
    print("  convert <input> <output>   - Convert between JSON/YAML formats")
    print("  stats <file>               - Show diagram statistics")


def main():
    """Main entry point"""
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
        sys.exit(0)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        if command == 'run':
            asyncio.run(CommandHandler.run(args))
        elif command == 'monitor':
            CommandHandler.monitor(args)
        elif command == 'convert':
            CommandHandler.convert(args)
        elif command == 'stats':
            CommandHandler.stats(args)
        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)
    
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to server at {API_URL}")
        print("Make sure the server is running: python -m apps.server.main")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()