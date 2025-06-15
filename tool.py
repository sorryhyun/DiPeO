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
import websockets
import requests
import os


# Constants
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/ws"
GRAPHQL_HOST = "localhost:8100"  # GraphQL server port
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


class DiagramValidator:
    """Validates diagram structure using Pydantic models"""
    
    @staticmethod
    def validate_diagram(diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Validate diagram using Pydantic DomainDiagram model"""
        try:
            # Import the Pydantic model
            from server.src.domain import DomainDiagram, DiagramMetadata
            from datetime import datetime
            
            # Ensure all required fields exist with proper defaults
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
            
            # Convert apiKeys to api_keys for Pydantic model
            if 'apiKeys' in diagram:
                diagram['api_keys'] = diagram.pop('apiKeys')
            
            # Validate using Pydantic model
            domain_diagram = DomainDiagram(**diagram)
            
            # Convert back to dict format expected by the rest of the code
            validated = domain_diagram.model_dump()
            
            # Convert api_keys back to apiKeys for backward compatibility
            if 'api_keys' in validated:
                validated['apiKeys'] = validated.pop('api_keys')
            
            return validated
            
        except ImportError:
            # Fallback to basic validation if imports fail
            print("⚠️  Warning: Could not import Pydantic models, using basic validation")
            return diagram
        except Exception as e:
            print(f"⚠️  Warning: Pydantic validation failed ({str(e)}), using basic structure")
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
    """Handles WebSocket-based diagram execution"""
    
    def __init__(self, options: ExecutionOptions):
        self.options = options
        self.node_timings = {} if options.debug else None
        self.last_activity_time = time.time()
    
    async def execute(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute diagram via WebSocket"""
        result = {
            "context": {},
            "total_token_count": 0,
            "messages": [],
            "execution_id": None
        }
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                await self._send_execution_request(websocket, diagram)
                result = await self._process_messages(websocket, result)
        except (websockets.exceptions.WebSocketException, ConnectionRefusedError):
            error_msg = f"Cannot connect to WebSocket at {WS_URL}. Make sure the server is running."
            print(f"❌ {error_msg}")
            result['error'] = error_msg
        except Exception as e:
            result['error'] = f"Execution error: {str(e)}"
        
        return result
    
    async def _send_execution_request(self, websocket, diagram: Dict[str, Any]) -> None:
        """Send execution request to WebSocket"""
        message = {
            "type": "execute_diagram",
            "diagram": diagram,
            "options": {
                "debugMode": self.options.debug,
                "stream": self.options.stream
            }
        }
        await websocket.send(json.dumps(message))
        
        if self.options.debug:
            print("🐛 Debug: Sent execution request via WebSocket")
            print(f"🐛 Debug: Activity timeout set to {self.options.timeout} seconds")
    
    async def _process_messages(self, websocket, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming WebSocket messages"""
        while True:
            try:
                # Wait for message with timeout
                elapsed = time.time() - self.last_activity_time
                remaining = max(0.1, self.options.timeout - elapsed)
                
                message = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                
            except asyncio.TimeoutError:
                print(f"\n⏱️  Timeout: No execution activity for {self.options.timeout} seconds")
                result['error'] = f"Execution timeout after {self.options.timeout} seconds of inactivity"
                break
            
            # Process message
            if await self._handle_message(message, result):
                break  # Execution complete
        
        return result
    
    async def _handle_message(self, message: str, result: Dict[str, Any]) -> bool:
        """Handle a single WebSocket message. Returns True if execution is complete."""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            # Skip connected message
            if msg_type == 'connected':
                return False
            
            # Update activity time for execution events
            if msg_type in {'node_start', 'node_progress', 'node_complete', 
                           'node_error', 'node_skipped', 'execution_started'}:
                self.last_activity_time = time.time()
            
            # Handle specific message types
            if msg_type == 'execution_started':
                result['execution_id'] = data.get('execution_id')
                if self.options.debug:
                    print(f"🚀 Execution started with ID: {result['execution_id']}")
            
            elif msg_type == 'node_start':
                self._handle_node_start(data)
            
            elif msg_type == 'node_complete':
                self._handle_node_complete(data, result)
            
            elif msg_type == 'node_error':
                self._handle_node_error(data)
            
            elif msg_type == 'execution_complete':
                self._handle_execution_complete(data, result)
                return True
            
            elif msg_type == 'execution_error':
                result['error'] = data.get('error', 'Unknown execution error')
                print(f"❌ Execution error: {result['error']}")
                return True
            
        except json.JSONDecodeError:
            if self.options.debug:
                print("🐛 Debug: Malformed JSON message")
        
        return False
    
    def _handle_node_start(self, data: Dict[str, Any]) -> None:
        """Handle node start event"""
        if not self.options.debug:
            return
        
        node_id = data.get('node_id', 'unknown')
        self.node_timings[node_id] = time.time()
        print(f"🐛 Starting node {node_id} ({data.get('node_type', 'unknown')})")
    
    def _handle_node_complete(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Handle node completion event"""
        node_id = data.get('node_id', 'unknown')
        
        # Track timing if debug mode
        if self.options.debug and node_id in self.node_timings:
            elapsed = time.time() - self.node_timings[node_id]
            print(f"✓ Node {node_id} completed in {elapsed:.2f}s")
        
        # Accumulate token count
        if 'token_count' in data:
            result['total_token_count'] += data['token_count']
        elif 'cost' in data:
            # Rough estimation from cost
            estimated_tokens = int(data['cost'] * 100000)
            result['total_token_count'] += estimated_tokens
    
    def _handle_node_error(self, data: Dict[str, Any]) -> None:
        """Handle node error event"""
        node_id = data.get('node_id', 'unknown')
        error = data.get('error', 'Unknown error')
        print(f"❌ Node {node_id} error: {error}")
    
    def _handle_execution_complete(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Handle execution complete event"""
        if 'data' in data:
            exec_data = data['data']
            result['context'] = exec_data.get('context', {})
            
            if 'total_token_count' in exec_data:
                result['total_token_count'] = exec_data['total_token_count']
            elif 'context' in exec_data and 'tokens' in exec_data['context']:
                tokens = exec_data['context']['tokens']
                result['total_token_count'] = tokens.get('input', 0) + tokens.get('output', 0)


class GraphQLExecutor:
    """Handles GraphQL-based diagram execution"""
    
    def __init__(self, options: ExecutionOptions):
        self.options = options
        self.node_timings = {} if options.debug else None
    
    async def execute(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute diagram via GraphQL"""
        try:
            from cli.graphql_client import DiPeoGraphQLClient
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
                
                # Subscribe to updates
                async for update in client.subscribe_to_execution(execution_id):
                    event_type = update['type']
                    
                    if self.options.debug:
                        print(f"🐛 Debug: Event '{event_type}' - {json.dumps(update, indent=2)}")
                    
                    # Handle different event types
                    if event_type == 'node_started' and self.options.stream:
                        node_id = update['nodeId']
                        print(f"\n🔄 Executing node: {node_id}")
                        if self.options.debug:
                            self.node_timings[node_id] = {'start': time.time()}
                    
                    elif event_type == 'node_completed':
                        await self._handle_node_completed(update, result)
                    
                    elif event_type == 'node_failed':
                        node_id = update['nodeId']
                        error = update.get('error', 'Unknown error')
                        print(f"❌ Node {node_id} failed: {error}")
                    
                    elif event_type == 'prompt_request':
                        # Handle interactive prompts
                        node_id = update['nodeId']
                        prompt = update.get('data', {}).get('prompt', 'Input required:')
                        print(f"\n💬 {prompt}")
                        user_input = input("Your response: ")
                        
                        await client.respond_to_prompt(execution_id, node_id, user_input)
                    
                    elif event_type == 'execution_completed':
                        result.update(update.get('data', {}))
                        if self.options.stream:
                            print("\n✨ Execution completed successfully!")
                        break
                    
                    elif event_type == 'execution_failed':
                        error = update.get('error', 'Unknown error')
                        raise Exception(f"Execution failed: {error}")
            
            except Exception as e:
                if self.options.debug:
                    print(f"❌ Error during execution: {str(e)}")
                result['error'] = str(e)
        
        return result
    
    async def _handle_node_completed(self, update: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Handle node completion event"""
        node_id = update['nodeId']
        node_result = update.get('data', {})
        
        if self.options.stream:
            print(f"✅ Node {node_id} completed")
            if node_result.get('output'):
                print(f"   Output: {node_result['output']}")
        
        if self.options.debug and node_id in self.node_timings:
            self.node_timings[node_id]['end'] = time.time()
            duration = self.node_timings[node_id]['end'] - self.node_timings[node_id]['start']
            print(f"   Duration: {duration:.2f}s")
        
        # Accumulate token count
        if 'token_count' in node_result:
            result['total_token_count'] += node_result['token_count']
        elif 'cost' in node_result:
            # Rough estimation from cost
            estimated_tokens = int(node_result['cost'] * 100000)
            result['total_token_count'] += estimated_tokens


class DiagramRunner:
    """Main diagram execution orchestrator"""
    
    def __init__(self, options: ExecutionOptions, use_graphql: bool = False):
        self.options = options
        # Use GraphQL if specified or if DIPEO_USE_GRAPHQL env var is set
        if use_graphql or os.environ.get('DIPEO_USE_GRAPHQL'):
            self.executor = GraphQLExecutor(options)
            if options.debug:
                print("🐛 Debug: Using GraphQL executor")
        else:
            self.executor = WebSocketExecutor(options)
            if options.debug:
                print("🐛 Debug: Using WebSocket executor")
    
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
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                message = {
                    "type": "broadcast_event",
                    "event": {
                        "type": "execution_started",
                        "execution_id": execution_id or f"cli_{uuid.uuid4().hex[:8]}",
                        "diagram": diagram,
                        "timestamp": datetime.now().isoformat(),
                        "from_cli": True
                    }
                }
                await websocket.send(json.dumps(message))
        except Exception:
            # Fallback to REST API if WebSocket fails
            pass


class CommandHandler:
    """Handles CLI commands"""
    
    @staticmethod
    async def run(args: List[str]) -> None:
        """Execute run command"""
        if not args:
            print("Error: Missing input file")
            sys.exit(1)
        
        file_path = args[0]
        options, use_graphql = CommandHandler._parse_run_options(args[1:])
        
        # Load diagram
        diagram = DiagramLoader.load(file_path)
        
        # Run diagram
        runner = DiagramRunner(options, use_graphql=use_graphql)
        result = await runner.run(diagram)
        
        print(f"✓ Execution complete - Total token count: {result.get('total_token_count', 0)}")
        
        # Save results
        CommandHandler._save_results(result, options)
    
    @staticmethod
    def _parse_run_options(args: List[str]) -> tuple[ExecutionOptions, bool]:
        """Parse command line options for run command"""
        options = ExecutionOptions()
        use_graphql = False
        
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
            elif arg == '--use-graphql':
                use_graphql = True
            elif arg.startswith('--timeout='):
                try:
                    options.timeout = int(arg.split('=')[1])
                except ValueError:
                    print("Error: Invalid timeout value. Using default.")
            elif not arg.startswith('--'):
                options.output_file = arg
        
        return options, use_graphql
    
    @staticmethod
    def _save_results(result: Dict[str, Any], options: ExecutionOptions) -> None:
        """Save execution results"""
        Path('files/results').mkdir(parents=True, exist_ok=True)
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
    print("  run <file> [options]       - 🚀 Run diagram")
    print("    --monitor               - Open browser monitor before execution")
    print("    --mode=headless         - Run without browser")
    print("    --no-browser            - Disable browser visualization")
    print("    --no-stream             - Disable streaming output")
    print("    --debug                 - Enable debug mode")
    print("    --timeout=<seconds>     - Set inactivity timeout (default: 300)")
    print("    --use-graphql           - Use GraphQL instead of WebSocket (experimental)")
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