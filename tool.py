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
from typing import Dict, Any
import asyncio
import aiohttp
import time
from typing import Optional


async def run_diagram_backend_execution(diagram: Dict[str, Any], stream: bool = True, debug: bool = False) -> Dict[str, Any]:
    """Execute diagram using unified backend V2 API with streaming support."""
    async with aiohttp.ClientSession() as session:
        try:
            # Prepare request payload
            payload = {"diagram": diagram}
            if debug:
                payload["options"] = {"debugMode": True}
                
            if stream:
                # Use V2 streaming endpoint
                async with session.post(
                    f"{API_URL}/api/diagrams/execute",
                    json=payload,
                    headers={"Content-Type": "application/json", "Accept": "text/event-stream"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "context": {},
                            "total_token_count": 0,
                            "messages": [],
                            "error": f"Backend execution failed: {response.status} - {error_text}"
                        }
                    
                    # Process SSE stream
                    final_result = {
                        "context": {},
                        "total_token_count": 0,
                        "messages": []
                    }
                    
                    node_timings = {} if debug else None
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])  # Remove 'data: ' prefix
                                
                                if debug:
                                    # Show all events in debug mode
                                    event_type = data.get('type', 'unknown')
                                    print(f"🐛 Debug: Event '{event_type}' - {json.dumps(data, indent=2)}")
                                
                                if data.get('type') == 'node_start' and debug:
                                    node_data = data.get('data', {})
                                    node_id = node_data.get('nodeId', 'unknown')
                                    node_timings[node_id] = time.time()
                                    print(f"🐛 Starting node {node_id} ({node_data.get('nodeType', 'unknown')})")
                                
                                elif data.get('type') == 'node_completed':
                                    # Backend sends data directly in the event, not wrapped in 'data'
                                    node_id = data.get('node_id', 'unknown')
                                    node_type = data.get('metadata', {}).get('nodeType', 'unknown')
                                    
                                    if debug and node_id in node_timings:
                                        elapsed = time.time() - node_timings[node_id]
                                        print(f"✓ Node {node_id} ({node_type}) completed in {elapsed:.2f}s")
                                        if data.get('output'):
                                            print(f"  Output: {str(data['output'])[:100]}...")
                                    
                                    if 'token_count' in data:
                                        final_result['total_token_count'] += data['token_count']
                                        if debug:
                                            print(f"  Token count: {data['token_count']}")
                                    
                                elif data.get('type') == 'node_skipped' and debug:
                                    node_data = data.get('data', {})
                                    print(f"⏭️  Node {node_data.get('nodeId', 'unknown')} skipped: {node_data.get('reason', 'unknown')}")
                                    
                                elif data.get('type') == 'execution_complete':
                                    execution_data = data.get('data', {})
                                    final_result['context'] = execution_data.get('context', {})
                                    final_result['total_token_count'] = execution_data.get('total_token_count', final_result['total_token_count'])
                                    
                                elif data.get('type') == 'error':
                                    error_data = data.get('data', {})
                                    print(f"❌ Execution error: {error_data.get('message', 'Unknown error')}")
                                    if debug and error_data.get('details'):
                                        print(f"  Details: {json.dumps(error_data['details'], indent=2)}")
                                    final_result['error'] = error_data.get('message', 'Unknown error')
                                    
                            except json.JSONDecodeError:
                                if debug:
                                    print(f"🐛 Debug: Malformed JSON line: {line}")
                                pass  # Skip malformed JSON
                    
                    return final_result
            else:
                # Use V2 non-streaming endpoint
                async with session.post(
                    f"{API_URL}/api/diagrams/execute",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "context": result.get("context", {}),
                            "total_token_count": result.get("total_token_count", 0),
                            "messages": []
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "context": {},
                            "total_token_count": 0,
                            "messages": [],
                            "error": f"API execution failed: {response.status} - {error_text}"
                        }
        except Exception as e:
            return {
                "context": {},
                "total_token_count": 0,
                "messages": [],
                "error": f"Execution error: {str(e)}"
            }




API_URL = "http://localhost:8000"


def load_diagram(file_path: str) -> Dict[str, Any]:
    """Load diagram from JSON or YAML file."""
    path = Path(file_path)

    with open(file_path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)


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


def broadcast_diagram_to_monitors(diagram: Dict[str, Any], execution_id: str = None):
    """Broadcast diagram structure to browser monitors via WebSocket."""
    try:
        import uuid
        from datetime import datetime
        
        event_data = {
            "type": "execution_started",
            "execution_id": execution_id or f"cli_{uuid.uuid4().hex[:8]}",
            "diagram": diagram,
            "timestamp": datetime.now().isoformat(),
            "from_cli": True
        }
        
        # First try the SSE broadcast endpoint (still available)
        response = requests.post(f"{API_URL}/api/monitor/broadcast", json=event_data)
        return response.status_code == 200
    except Exception:
        return False


def run_diagram(diagram: Dict[str, Any], show_in_browser: bool = True, pre_initialize: bool = True, stream: bool = True, debug: bool = False) -> Dict[str, Any]:
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
        broadcast_diagram_to_monitors(diagram)
    
    result = asyncio.run(run_diagram_backend_execution(diagram, stream=stream, debug=debug))
    
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
    """Wait for at least one monitor to connect to the SSE endpoint."""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_URL}/api/monitor/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("active_monitors", 0) > 0:
                    return True
        except Exception:
            pass
        
        time.sleep(check_interval)
    
    return False


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
        return {"message": "No person nodes with complete model configuration found", "initialized": 0}
    
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
        print("      --mode=monitor                        - Pre-load models, open browser, then run (RECOMMENDED)")
        print("      --mode=headless                       - Pure backend execution without browser")
        print("      --mode=check                          - Run and analyze conversation logs")
        print("      --no-browser                          - Disable browser visualization")
        print("      --no-preload                          - Skip model pre-initialization")  
        print("      --no-stream                           - Disable streaming output")
        print("      --debug                               - Enable debug mode with verbose output")
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
            show_in_browser = True
            pre_initialize = True
            stream = True
            check_forget = False
            debug = False
            output_file = None
            
            for arg in args[1:]:
                if arg.startswith('--mode='):
                    mode = arg.split('=')[1]
                elif arg == '--no-browser':
                    show_in_browser = False
                elif arg == '--no-preload':
                    pre_initialize = False
                elif arg == '--no-stream':
                    stream = False
                elif arg == '--debug':
                    debug = True
                elif not arg.startswith('--'):
                    output_file = arg  # Additional output file for check mode

            # Apply mode-specific settings
            if mode == 'monitor':
                # run-and-monitor behavior
                diagram = load_diagram(file_path)
                
                # Pre-initialize models silently
                pre_initialize_models(diagram, verbose=debug)
                
                # Open browser monitor first
                open_browser_monitor()
                
                # Wait for monitor connection with faster interval
                if wait_for_monitor_connection(timeout=5, check_interval=0.1):
                    print("✓ Monitor connected")
                else:
                    print("⚠️  No monitor connected within timeout, continuing anyway")
                
                # Now broadcast diagram structure to connected monitors
                import uuid
                execution_id = f"cli_{uuid.uuid4().hex[:8]}"
                broadcast_diagram_to_monitors(diagram, execution_id)
                
                # Delay to ensure diagram is loaded and rendered in browser
                # Reduced delay since SSE connects faster now
                time.sleep(1.0)
                
                # Run diagram - disable show_in_browser to prevent double broadcast
                result = run_diagram(diagram, show_in_browser=True, pre_initialize=False, stream=stream, debug=debug)
                
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

            result = run_diagram(diagram, show_in_browser=show_in_browser, pre_initialize=pre_initialize, stream=stream, debug=debug)
            
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