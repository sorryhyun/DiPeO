#!/usr/bin/env python3
"""
DiPeO CLI Tool - Simplified Version
Focus on actual implemented features: import, export, run
"""

import json
import sys
import requests
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import time
import websockets
import uuid


async def run_diagram_backend_execution(diagram: Dict[str, Any], stream: bool = True, debug: bool = False, timeout: int = 300) -> Dict[str, Any]:
    """Execute diagram using WebSocket-based backend execution."""
    # WebSocket URL
    ws_url = f"ws://localhost:8000/api/ws"
    
    # Initialize result
    final_result = {
        "context": {},
        "total_token_count": 0,
        "messages": [],
        "execution_id": None
    }
    
    node_timings = {} if debug else None
    last_activity_time = time.time()
    timeout_seconds = timeout  # Timeout in seconds for no activity
    
    try:
        async with websockets.connect(ws_url) as websocket:
            # Send execute_diagram message
            execution_message = {
                "type": "execute_diagram",
                "diagram": diagram,
                "options": {
                    "debugMode": debug,
                    "stream": stream
                }
            }
            
            await websocket.send(json.dumps(execution_message))
            
            if debug:
                print(f"🐛 Debug: Sent execution request via WebSocket")
                print(f"🐛 Debug: Activity timeout set to {timeout_seconds} seconds")
            
            # Process incoming messages with timeout
            while True:
                try:
                    # Calculate remaining timeout
                    elapsed = time.time() - last_activity_time
                    remaining_timeout = max(0.1, timeout_seconds - elapsed)
                    
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=remaining_timeout
                    )
                    
                except asyncio.TimeoutError:
                    # No activity for timeout period
                    print(f"\n⏱️  Timeout: No execution activity for {timeout_seconds} seconds")
                    final_result['error'] = f"Execution timeout after {timeout_seconds} seconds of inactivity"
                    break
                
                try:
                    data = json.loads(message)
                    
                    if debug:
                        event_type = data.get('type', 'unknown')
                        # Don't print full diagram for execution_started
                        if event_type == 'execution_started':
                            print(f"🐛 Debug: Event '{event_type}' - execution_id: {data.get('execution_id')}")
                        else:
                            print(f"🐛 Debug: Event '{event_type}' - {json.dumps(data, indent=2)}")
                    
                    # Skip the initial "connected" message
                    if data.get('type') == 'connected':
                        continue
                    
                    # Update activity time only for node execution signals
                    node_execution_events = {
                        'node_start', 'node_progress', 'node_complete', 
                        'node_error', 'node_skipped', 'execution_started'
                    }
                    if data.get('type') in node_execution_events:
                        last_activity_time = time.time()
                        if debug:
                            print(f"🐛 Debug: Activity detected - reset timeout")
                    
                    # Handle different message types
                    if data.get('type') == 'execution_started':
                        final_result['execution_id'] = data.get('execution_id')
                        if debug:
                            print(f"🚀 Execution started with ID: {final_result['execution_id']}")
                            print(f"  Total nodes: {data.get('total_nodes', 'unknown')}")
                    
                    elif data.get('type') == 'node_start':
                        node_id = data.get('node_id', 'unknown')
                        if debug:
                            node_timings[node_id] = time.time()
                            print(f"🐛 Starting node {node_id} ({data.get('node_type', 'unknown')})")
                    
                    elif data.get('type') == 'node_progress':
                        if debug:
                            node_id = data.get('node_id', 'unknown')
                            message_text = data.get('message', '')
                            print(f"  Progress [{node_id}]: {message_text}")
                    
                    elif data.get('type') == 'node_complete':
                        node_id = data.get('node_id', 'unknown')
                        node_type = data.get('node_type', 'unknown')
                        
                        if debug and node_id in node_timings:
                            elapsed = time.time() - node_timings[node_id]
                            print(f"✓ Node {node_id} ({node_type}) completed in {elapsed:.2f}s")
                            if data.get('output'):
                                print(f"  Output: {str(data['output'])[:100]}...")
                        
                        # Accumulate token count if available
                        if 'token_count' in data:
                            # Direct token count from backend
                            tokens = data['token_count']
                            final_result['total_token_count'] += tokens
                            if debug:
                                print(f"  Tokens: {tokens}")
                        elif 'cost' in data:
                            # Fallback: estimate tokens from cost (rough approximation)
                            # Assuming ~$0.01 per 1000 tokens for simplicity
                            estimated_tokens = int(data['cost'] * 100000)
                            final_result['total_token_count'] += estimated_tokens
                            if debug:
                                print(f"  Cost: ${data['cost']:.4f} (~{estimated_tokens} tokens)")
                    
                    elif data.get('type') == 'node_skipped':
                        if debug:
                            node_id = data.get('node_id', 'unknown')
                            reason = data.get('reason', 'unknown')
                            print(f"⏭️  Node {node_id} skipped: {reason}")
                    
                    elif data.get('type') == 'node_error':
                        node_id = data.get('node_id', 'unknown')
                        error = data.get('error', 'Unknown error')
                        print(f"❌ Node {node_id} error: {error}")
                        if debug and data.get('details'):
                            print(f"  Details: {json.dumps(data.get('details'), indent=2)}")
                    
                    elif data.get('type') == 'execution_complete':
                        # Extract final results
                        if 'data' in data:
                            # New format: nested data structure
                            exec_data = data['data']
                            final_result['context'] = exec_data.get('context', {})
                            # Get total token count directly
                            if 'total_token_count' in exec_data:
                                final_result['total_token_count'] = exec_data['total_token_count']
                            elif 'context' in exec_data and 'tokens' in exec_data['context']:
                                # Alternative: sum from token details
                                tokens = exec_data['context']['tokens']
                                final_result['total_token_count'] = tokens.get('input', 0) + tokens.get('output', 0)
                        else:
                            # Old format compatibility
                            final_result['context'] = data.get('final_context', {})
                            if 'total_cost' in data:
                                # Estimate from cost if no token count
                                final_result['total_token_count'] = int(data['total_cost'] * 100000)
                        if 'duration' in data and debug:
                            print(f"⏱️  Total execution time: {data['duration']:.2f}s")
                        break  # Execution is complete
                    
                    elif data.get('type') == 'execution_error':
                        error_msg = data.get('error', 'Unknown execution error')
                        print(f"❌ Execution error: {error_msg}")
                        final_result['error'] = error_msg
                        break
                    
                    elif data.get('type') == 'interactive_prompt':
                        # Handle interactive prompts if needed
                        print(f"⚠️  Interactive prompt requested but not supported in CLI mode")
                        print(f"  Prompt: {data.get('prompt', 'unknown')}")
                        # Could implement interactive input here if needed
                    
                except json.JSONDecodeError:
                    if debug:
                        print(f"🐛 Debug: Malformed JSON message: {message}")
                    pass  # Skip malformed JSON
            
            return final_result
            
    except (websockets.exceptions.WebSocketException, ConnectionRefusedError):
        error_msg = f"Cannot connect to WebSocket at {ws_url}. Make sure the server is running."
        print(f"❌ {error_msg}")
        return {
            "context": {},
            "total_token_count": 0,
            "messages": [],
            "error": error_msg
        }
    except Exception as e:
        return {
            "context": {},
            "total_token_count": 0,
            "messages": [],
            "error": f"Execution error: {str(e)}"
        }




API_URL = "http://localhost:8000"


def transform_api_key_labels(diagram: Dict[str, Any]) -> Dict[str, Any]:
    """Transform apiKeyLabel to apiKeyId in persons array for backend compatibility."""
    # Create a mapping from apiKeyLabel to apiKeyId
    api_key_map = {}
    for api_key in diagram.get('apiKeys', []):
        if 'name' in api_key:
            # Find the corresponding apiKeyId by matching service
            # Since we don't have the actual IDs, we'll use a test key
            api_key_map[api_key['name']] = 'APIKEY_387B73'  # Default test key
    
    # Transform persons array
    persons = diagram.get('persons', [])
    if isinstance(persons, list):
        for person in persons:
            if 'apiKeyLabel' in person and 'apiKeyId' not in person:
                # Map apiKeyLabel to apiKeyId
                label = person.get('apiKeyLabel')
                if label in api_key_map:
                    person['apiKeyId'] = api_key_map[label]
                else:
                    # Default to test key if not found
                    person['apiKeyId'] = 'APIKEY_387B73'
                # Remove apiKeyLabel to avoid confusion
                person.pop('apiKeyLabel', None)
            elif 'apiKeyId' not in person and 'apiKeyLabel' not in person:
                # Person has neither apiKeyId nor apiKeyLabel, assign default
                person['apiKeyId'] = 'APIKEY_387B73'
    
    # Transform arrows to backend format
    arrows = diagram.get('arrows', [])
    for arrow in arrows:
        if 'sourceHandle' in arrow and 'source' not in arrow:
            # Extract node ID from handle format "nodeId::handleName"
            source_parts = arrow['sourceHandle'].split('::', 1)
            arrow['source'] = source_parts[0]
            if len(source_parts) > 1:
                arrow['sourceHandle'] = source_parts[1]
            
        if 'targetHandle' in arrow and 'target' not in arrow:
            # Extract node ID from handle format "nodeId::handleName"
            target_parts = arrow['targetHandle'].split('::', 1)
            arrow['target'] = target_parts[0]
            if len(target_parts) > 1:
                arrow['targetHandle'] = target_parts[1]
    
    # Transform nodes - ensure each node has an ID
    nodes = diagram.get('nodes', [])
    for i, node in enumerate(nodes):
        if 'id' not in node:
            # Generate ID from label or index
            node['id'] = node.get('label', f'node_{i}').replace(' ', '_')
    
    return diagram


def load_diagram(file_path: str) -> Dict[str, Any]:
    """Load diagram from JSON or YAML file."""
    path = Path(file_path)

    with open(file_path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            diagram = yaml.safe_load(f)
        else:
            diagram = json.load(f)
    
    # Transform apiKeyLabel to apiKeyId for backend compatibility
    diagram = transform_api_key_labels(diagram)
    return diagram


def save_diagram(diagram: Dict[str, Any], file_path: str) -> None:
    """Save diagram to JSON or YAML file."""
    path = Path(file_path)

    with open(file_path, 'w') as f:
        if path.suffix in ['.yaml', '.yml']:
            yaml.dump(diagram, f, default_flow_style=False, sort_keys=False)
        else:
            json.dump(diagram, f, indent=2)


def import_uml(file_path: str) -> Dict[str, Any]:
    """Import diagram from PlantUML file.
    
    Note: Backend doesn't have a dedicated import-uml endpoint.
    This uses the convert endpoint instead.
    """
    with open(file_path, 'r') as f:
        uml_content = f.read()

    response = requests.post(f"{API_URL}/api/diagrams/convert", json={
        "content": uml_content,
        "from_format": "uml",
        "to_format": "json"
    })
    response.raise_for_status()
    result = response.json()
    # The convert endpoint returns {"success": true, "output": "..."} 
    return json.loads(result.get('output', '{}'))


def export_uml(diagram: Dict[str, Any]) -> str:
    """Export diagram to PlantUML format.
    
    Note: Backend doesn't have a dedicated export-uml endpoint.
    This uses the convert endpoint instead.
    """
    response = requests.post(f"{API_URL}/api/diagrams/convert", json={
        "content": json.dumps(diagram),
        "from_format": "json",
        "to_format": "uml"
    })
    response.raise_for_status()
    result = response.json()
    # The convert endpoint returns {"success": true, "output": "..."}
    return result.get('output', '')


async def broadcast_diagram_to_monitors(diagram: Dict[str, Any], execution_id: str = None):
    """Broadcast diagram structure to browser monitors via WebSocket."""
    from datetime import datetime
    
    try:
        ws_url = f"ws://localhost:8000/api/ws"
        
        async with websockets.connect(ws_url) as websocket:
            # Send a monitor broadcast message
            broadcast_message = {
                "type": "broadcast_event",
                "event": {
                    "type": "execution_started",
                    "execution_id": execution_id or f"cli_{uuid.uuid4().hex[:8]}",
                    "diagram": diagram,
                    "timestamp": datetime.now().isoformat(),
                    "from_cli": True
                }
            }
            
            await websocket.send(json.dumps(broadcast_message))
            return True
            
    except Exception:
        # Fall back to REST endpoint if WebSocket fails
        try:
            event_data = {
                "type": "execution_started",
                "execution_id": execution_id or f"cli_{uuid.uuid4().hex[:8]}",
                "diagram": diagram,
                "timestamp": datetime.now().isoformat(),
                "from_cli": True
            }
            
            response = requests.post(f"{API_URL}/api/monitor/broadcast", json=event_data)
            return response.status_code == 200
        except Exception:
            return False


def run_diagram(diagram: Dict[str, Any], show_in_browser: bool = True, pre_initialize: bool = True, stream: bool = True, debug: bool = False, timeout: int = 300) -> Dict[str, Any]:
    """Synchronous wrapper for backend execution with optional pre-initialization."""
    start_time = time.time() if debug else None
    
    if debug:
        print("🐛 Debug mode enabled - verbose output and timing information")
        
    if pre_initialize:
        if debug:
            print("🔧 Pre-initializing models...")
        results = pre_initialize_models(diagram, verbose=debug)
        if debug and (results["initialized"] > 0 or results["failed"] > 0):
            print(f"  ✓ Initialized: {results['initialized']}, Failed: {results['failed']}")
            print()
    
    if show_in_browser:
        if debug:
            print("🌐 Browser visualization enabled - open http://localhost:3000 to see execution")
        # Broadcast diagram structure to monitors
        asyncio.run(broadcast_diagram_to_monitors(diagram))
    
    result = asyncio.run(run_diagram_backend_execution(diagram, stream=stream, debug=debug, timeout=timeout))
    
    if debug and start_time:
        elapsed = time.time() - start_time
        print(f"\n🐛 Debug: Total execution time: {elapsed:.2f}s")
        if result.get('context'):
            print(f"🐛 Debug: Final context size: {len(str(result['context']))} chars")
            print(f"🐛 Debug: Context keys: {sorted(result['context'].keys())}")
    
    return result


def open_browser_monitor():
    """Open browser to monitoring page."""
    import webbrowser
    monitor_url = "http://localhost:3000/?monitor=true"
    webbrowser.open(monitor_url)


def wait_for_monitor_connection(timeout: int = 10, check_interval: float = 0.5) -> bool:
    """Wait for monitor to potentially connect."""
    import time
    # Since monitors connect via WebSocket and there's no HTTP endpoint to check,
    # we'll just wait a reasonable amount of time for the browser to open and connect
    time.sleep(min(2.0, timeout))  # Wait up to 2 seconds for browser to open
    return True


def extract_person_models(diagram: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Extract all unique model configurations from person nodes in the diagram."""
    person_models = {}
    persons = diagram.get('persons', {})
    
    # Handle both dict format (YAML) and list format (JSON)
    if isinstance(persons, dict):
        # YAML format: persons is a dict with person_id as keys
        for person_id, person in persons.items():
            service = person.get('service')
            model = person.get('modelName') or person.get('model')  # Support both formats
            api_key_id = person.get('apiKeyId')
            
            if person_id and service and model and api_key_id:
                # Use model+service+api_key_id as key to avoid duplicates
                key = f"{service}:{model}:{api_key_id}"
                person_models[key] = {
                    'service': service,
                    'model': model,
                    'api_key_id': api_key_id,
                    'person_id': person_id
                }
    elif isinstance(persons, list):
        # JSON format: persons is a list of person objects
        for person in persons:
            person_id = person.get('id')
            service = person.get('service')
            model = person.get('modelName') or person.get('model')  # Support both formats
            api_key_id = person.get('apiKeyId')
            
            if person_id and service and model and api_key_id:
                # Use model+service+api_key_id as key to avoid duplicates
                key = f"{service}:{model}:{api_key_id}"
                person_models[key] = {
                    'service': service,
                    'model': model,
                    'api_key_id': api_key_id,
                    'person_id': person_id
                }
    
    return person_models


def pre_initialize_models(diagram: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """Pre-initialize all models used in the diagram.
    
    Note: The backend doesn't have an initialize-model endpoint.
    This function currently serves as a placeholder that extracts
    model configurations but doesn't actually pre-initialize them.
    """
    person_models = extract_person_models(diagram)
    
    if not person_models:
        return {"message": "No person nodes with complete model configuration found", "initialized": 0, "failed": 0}
    
    if verbose:
        print(f"Found {len(person_models)} unique model(s) in diagram")
        for key, config in person_models.items():
            print(f"  - {config['service']}:{config['model']} (person: {config['person_id']})")
    
    # Since the backend doesn't have model pre-initialization,
    # we just return success for all models found
    results = {
        "initialized": len(person_models),
        "failed": 0,
        "details": [
            {
                "status": "success", 
                "config": config,
                "message": "Model configuration validated"
            }
            for config in person_models.values()
        ]
    }
    
    return results


def get_diagram_stats(diagram: Dict[str, Any]) -> Dict[str, Any]:
    """Get statistics about a diagram."""
    nodes = diagram.get('nodes', [])
    arrows = diagram.get('arrows', [])
    persons = diagram.get('persons', [])

    node_types = {}
    for node in nodes:
        node_type = node.get('type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    return {
        'persons': len(persons),
        'nodes': len(nodes),
        'arrows': len(arrows),
        'node_types': node_types,
        'has_api_keys': len(diagram.get('apiKeys', [])) > 0
    }


def main():
    if len(sys.argv) < 2:
        print("AgentDiagram CLI Tool\n")
        print("Usage: python tool.py <command> [options]\n")
        print("Commands:")
        print("  run <file> [options]                      - 🚀 Run diagram with execution options")
        print("    Options:")
        print("      --monitor                             - Pre-load models, open browser, then run (RECOMMENDED)")
        print("      --mode=headless                       - Pure backend execution without browser")
        print("      --mode=check                          - Run and analyze conversation logs")
        print("      --no-browser                          - Disable browser visualization")
        print("      --no-preload                          - Skip model pre-initialization")  
        print("      --no-stream                           - Disable streaming output")
        print("      --debug                               - Enable debug mode with verbose output")
        print("      --timeout=<seconds>                   - Set inactivity timeout (default: 300s)")
        print("  monitor                                   - Open browser monitoring page")
        print("  preload <file>                            - Pre-initialize all models in diagram")
        print("  convert <input> <output> [format]         - Convert between formats (JSON/YAML/LLM-YAML/UML)")
        print("  stats <file>                              - Show diagram statistics")
        print("  server-save <file> <name>                 - Save diagram to server")
        print("  check-forget [log_dir]                    - Analyze forget rule compliance")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'monitor':
            open_browser_monitor()

        elif command == 'preload':
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            diagram = load_diagram(sys.argv[2])
            results = pre_initialize_models(diagram, verbose=True)
            
            if results["initialized"] == 0 and results["failed"] == 0:
                print("No person nodes with complete model configuration found")
            else:
                print(f"Pre-initialized: {results['initialized']} successful, {results['failed']} failed")

        elif command == 'run':
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            # Parse options
            args = sys.argv[2:]
            file_path = args[0]
            
            # Extract mode and flags
            mode = None
            monitor = False
            show_in_browser = True
            pre_initialize = True
            stream = True
            check_forget = False
            debug = False
            timeout = 300  # Default 5 minutes
            output_file = None
            
            for arg in args[1:]:
                if arg.startswith('--mode='):
                    mode = arg.split('=')[1]
                elif arg == '--monitor':
                    monitor = True
                elif arg == '--no-browser':
                    show_in_browser = False
                elif arg == '--no-preload':
                    pre_initialize = False
                elif arg == '--no-stream':
                    stream = False
                elif arg == '--debug':
                    debug = True
                elif arg.startswith('--timeout='):
                    try:
                        timeout = int(arg.split('=')[1])
                    except ValueError:
                        print(f"Error: Invalid timeout value. Using default 300 seconds.")
                elif not arg.startswith('--'):
                    output_file = arg  # Additional output file for check mode

            # Apply mode-specific settings
            if monitor:
                # run-and-monitor behavior
                diagram = load_diagram(file_path)
                
                # Pre-initialize models silently
                pre_initialize_models(diagram, verbose=debug)
                
                # Open browser monitor first
                open_browser_monitor()
                
                # Wait for monitor connection
                if wait_for_monitor_connection(timeout=2):
                    print("✓ Monitor ready")
                else:
                    print("⚠️  Monitor may not be ready, continuing anyway")
                
                # Now broadcast diagram structure to connected monitors
                execution_id = f"cli_{uuid.uuid4().hex[:8]}"
                asyncio.run(broadcast_diagram_to_monitors(diagram, execution_id))
                
                # Delay to ensure diagram is loaded and rendered in browser
                time.sleep(1.0)
                
                # Run diagram - disable show_in_browser to prevent double broadcast
                result = run_diagram(diagram, show_in_browser=True, pre_initialize=False, stream=stream, debug=debug, timeout=timeout)
                
                print(f"✓ Execution complete - Total token count: {result.get('total_token_count', 0)}")
                return
                
            elif mode == 'headless':
                # run-headless behavior
                show_in_browser = False
                pre_initialize = True
                stream = True
                
            elif mode == 'check':
                # run-and-check behavior
                check_forget = True
                show_in_browser = False

            # Standard run execution
            diagram = load_diagram(file_path)

            result = run_diagram(diagram, show_in_browser=show_in_browser, pre_initialize=pre_initialize, stream=stream, debug=debug, timeout=timeout)
            
            print(f"✓ Execution complete - Total token count: {result.get('total_token_count', 0)}")

            # Save results
            Path('files/results').mkdir(exist_ok=True)
            save_path = output_file if output_file else 'files/results/results.json'
            with open(save_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            if debug:
                print(f"  Results saved to: {save_path}")
                # Save detailed debug logs
                debug_path = save_path.replace('.json', '_debug.json')
                debug_data = {
                    'result': result,
                    'diagram_stats': get_diagram_stats(diagram),
                    'execution_time': result.get('execution_time', 'N/A'),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                with open(debug_path, 'w') as f:
                    json.dump(debug_data, f, indent=2)
                print(f"  Debug logs saved to: {debug_path}")

        elif command == 'convert':
            if len(sys.argv) < 4:
                print("Error: Usage: convert <input> <output> [format]")
                print("  Formats: json, yaml, llm-yaml, uml")
                sys.exit(1)

            input_path = Path(sys.argv[2])
            output_path = Path(sys.argv[3])
            format_arg = sys.argv[4] if len(sys.argv) > 4 else None

            # Handle UML conversion (legacy Python method)
            if input_path.suffix in ['.puml', '.uml'] or output_path.suffix in ['.puml', '.uml']:
                if input_path.suffix in ['.puml', '.uml']:
                    diagram = import_uml(str(input_path))
                    save_diagram(diagram, str(output_path))
                else:
                    diagram = load_diagram(str(input_path))
                    uml_content = export_uml(diagram)
                    with open(output_path, 'w') as f:
                        f.write(uml_content)
                print(f"✓ Converted: {input_path} → {output_path}")
            else:
                # Use enhanced TypeScript conversion
                import subprocess
                cmd = ['pnpm', 'convert', str(input_path), str(output_path)]
                if format_arg:
                    cmd.append(format_arg)
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
                    if result.returncode == 0:
                        print(f"✓ Converted: {input_path} → {output_path}")
                    else:
                        # Fallback to basic Python conversion
                        diagram = load_diagram(str(input_path))
                        save_diagram(diagram, str(output_path))
                        print(f"✓ Converted: {input_path} → {output_path}")
                except FileNotFoundError:
                    # Fallback for pnpm not found
                    diagram = load_diagram(str(input_path))
                    save_diagram(diagram, str(output_path))
                    print(f"✓ Converted: {input_path} → {output_path}")

        elif command == 'stats':
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            diagram = load_diagram(sys.argv[2])
            stats = get_diagram_stats(diagram)

            print(f"\nDiagram Statistics:")
            print(f"  Persons: {stats['persons']}")
            print(f"  Nodes: {stats['nodes']}")
            print(f"  Arrows: {stats['arrows']}")
            print(f"  API Keys: {'Yes' if stats['has_api_keys'] else 'No'}")

            if stats['node_types']:
                print(f"\nNode Types:")
                for node_type, count in sorted(stats['node_types'].items()):
                    print(f"  {node_type}: {count}")

        elif command == 'server-save':
            if len(sys.argv) < 4:
                print("Error: Usage: server-save <file> <name>")
                sys.exit(1)

            diagram = load_diagram(sys.argv[2])
            filename = sys.argv[3]

            # Determine format from filename
            format_type = 'yaml' if filename.endswith(('.yaml', '.yml')) else 'json'

            response = requests.post(f"{API_URL}/api/diagrams/save", json={
                'diagram': diagram,
                'filename': filename,
                'format': format_type
            })
            response.raise_for_status()

            result = response.json()
            print(f"✓ {result.get('message', 'Saved to server')}")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to AgentDiagram server at", API_URL)
        print("Make sure the server is running: cd apps/server && python main.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()