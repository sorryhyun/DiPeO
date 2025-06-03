#!/usr/bin/env python3
"""
AgentDiagram CLI Tool - Simplified Version
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
                    f"{API_URL}/api/run-diagram",
                    json=payload,
                    headers={"Content-Type": "application/json", "Accept": "text/event-stream"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "context": {},
                            "total_cost": 0,
                            "messages": [],
                            "error": f"Backend execution failed: {response.status} - {error_text}"
                        }
                    
                    # Process SSE stream
                    final_result = {
                        "context": {},
                        "total_cost": 0,
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
                                    if event_type not in ['execution_started', 'execution_complete', 'node_complete', 'error']:
                                        print(f"🐛 Debug: Event '{event_type}' - {json.dumps(data.get('data', {}), indent=2)}")
                                
                                if data.get('type') == 'node_start' and debug:
                                    node_data = data.get('data', {})
                                    node_id = node_data.get('nodeId', 'unknown')
                                    node_timings[node_id] = time.time()
                                    print(f"🐛 Starting node {node_id} ({node_data.get('nodeType', 'unknown')})")
                                
                                elif data.get('type') == 'node_complete':
                                    node_data = data.get('data', {})
                                    node_id = node_data.get('nodeId', 'unknown')
                                    node_type = node_data.get('nodeType', 'unknown')
                                    
                                    if debug and node_id in node_timings:
                                        elapsed = time.time() - node_timings[node_id]
                                        print(f"✓ Node {node_id} ({node_type}) completed in {elapsed:.2f}s")
                                        if node_data.get('output'):
                                            print(f"  Output: {str(node_data['output'])[:100]}...")
                                    
                                    if 'cost' in node_data:
                                        final_result['total_cost'] += node_data['cost']
                                        if debug:
                                            print(f"  Cost: ${node_data['cost']:.4f}")
                                    
                                elif data.get('type') == 'node_skipped' and debug:
                                    node_data = data.get('data', {})
                                    print(f"⏭️  Node {node_data.get('nodeId', 'unknown')} skipped: {node_data.get('reason', 'unknown')}")
                                    
                                elif data.get('type') == 'execution_complete':
                                    execution_data = data.get('data', {})
                                    final_result['context'] = execution_data.get('context', {})
                                    final_result['total_cost'] = execution_data.get('totalCost', final_result['total_cost'])
                                    
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
                    f"{API_URL}/api/run-diagram",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "context": result.get("context", {}),
                            "total_cost": result.get("total_cost", 0),
                            "messages": []
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "context": {},
                            "total_cost": 0,
                            "messages": [],
                            "error": f"API execution failed: {response.status} - {error_text}"
                        }
        except Exception as e:
            return {
                "context": {},
                "total_cost": 0,
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
    """Import diagram from PlantUML file."""
    with open(file_path, 'r') as f:
        uml_content = f.read()

    response = requests.post(f"{API_URL}/api/import-uml", json={"uml": uml_content})
    response.raise_for_status()
    return response.json()


def export_uml(diagram: Dict[str, Any]) -> str:
    """Export diagram to PlantUML format."""
    response = requests.post(f"{API_URL}/api/export-uml", json=diagram)
    response.raise_for_status()
    return response.text


def broadcast_diagram_to_monitors(diagram: Dict[str, Any], execution_id: str = None):
    """Broadcast diagram structure to browser monitors."""
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


def analyze_conversation_logs(log_dir: str = "conversation_logs") -> Dict[str, Any]:
    """Analyze conversation logs to check if forget rules are properly followed."""
    log_path = Path(log_dir)
    if not log_path.exists():
        return {"error": f"Log directory {log_dir} does not exist"}
    
    analysis = {
        "total_conversations": 0,
        "forget_rule_violations": [],
        "forget_rule_compliance": [],
        "summary": {}
    }
    
    # Find all conversation log files (both .json and .jsonl formats)
    log_files = list(log_path.glob("*.json")) + list(log_path.glob("*.jsonl"))
    analysis["total_conversations"] = len(log_files)
    
    for log_file in log_files:
        try:
            messages = []
            
            # Handle both JSON and JSONL formats
            if log_file.suffix == '.jsonl':
                with open(log_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            if data.get("type") == "message":
                                messages.append(data)
            else:
                with open(log_file, 'r') as f:
                    conversation = json.load(f)
                    messages = conversation.get("messages", [])
            
            # Check if conversation follows the forget rule:
            # "person only remembers what the previous person said and the prompt given to them"
            
            for i, message in enumerate(messages):
                person_id = message.get("sender_person_id")
                if not person_id:
                    continue
                
                # Check if this person's message references anything beyond:
                # 1. The previous person's message
                # 2. The prompt given to them
                if i > 1:  # Skip first message
                    current_content = message.get("content", "").lower()
                    
                    # Look for references to messages from more than 1 turn ago
                    # This is a simple heuristic - could be made more sophisticated
                    violation_indicators = [
                        "as i mentioned earlier",
                        "as we discussed before",
                        "going back to what",
                        "earlier you said",
                        "previously mentioned"
                    ]
                    
                    has_violation = any(indicator in current_content for indicator in violation_indicators)
                    
                    if has_violation:
                        analysis["forget_rule_violations"].append({
                            "file": str(log_file),
                            "message_index": i,
                            "person_id": person_id,
                            "content_preview": current_content[:100] + "..."
                        })
                    else:
                        analysis["forget_rule_compliance"].append({
                            "file": str(log_file),
                            "message_index": i,
                            "person_id": person_id
                        })
        
        except Exception as e:
            print(f"Error analyzing {log_file}: {e}")
    
    analysis["summary"] = {
        "compliance_rate": len(analysis["forget_rule_compliance"]) / max(1, len(analysis["forget_rule_compliance"]) + len(analysis["forget_rule_violations"])),
        "total_violations": len(analysis["forget_rule_violations"]),
        "total_compliant": len(analysis["forget_rule_compliance"])
    }
    
    return analysis

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
    """Pre-initialize all models used in the diagram."""
    person_models = extract_person_models(diagram)
    
    if not person_models:
        return {"message": "No person nodes with complete model configuration found", "initialized": 0}
    
    if verbose:
        print(f"Pre-initializing {len(person_models)} unique model(s)...")
    
    results = {
        "initialized": 0,
        "failed": 0,
        "details": []
    }
    
    for key, config in person_models.items():
        try:
            response = requests.post(f"{API_URL}/api/initialize-model", json={
                'service': config['service'],
                'model': config['model'],
                'api_key_id': config['api_key_id']
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    if verbose:
                        print(f"  ✓ {config['service']}:{config['model']} (person: {config['person_id']})")
                    results["initialized"] += 1
                    results["details"].append({
                        "status": "success", 
                        "config": config,
                        "message": data.get('message', '')
                    })
                else:
                    if verbose:
                        print(f"  ❌ {config['service']}:{config['model']} - {data.get('error', 'Unknown error')}")
                    results["failed"] += 1
                    results["details"].append({
                        "status": "failed",
                        "config": config, 
                        "error": data.get('error', 'Unknown error')
                    })
            else:
                if verbose:
                    print(f"  ❌ {config['service']}:{config['model']} - HTTP {response.status_code}")
                results["failed"] += 1
                results["details"].append({
                    "status": "failed",
                    "config": config,
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            if verbose:
                print(f"  ❌ {config['service']}:{config['model']} - {str(e)}")
            results["failed"] += 1
            results["details"].append({
                "status": "failed",
                "config": config,
                "error": str(e)
            })
    
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
                
                # Open browser monitor
                open_browser_monitor()
                time.sleep(2)
                
                result = run_diagram(diagram, show_in_browser=True, pre_initialize=False, stream=stream, debug=debug)
                
                print(f"✓ Execution complete - Total cost: ${result.get('total_cost', 0):.4f}")
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
            
            print(f"✓ Execution complete - Total cost: ${result.get('total_cost', 0):.4f}")

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
            
            # Check forget rules if requested
            if check_forget:
                print(f"\n🔍 Checking forget rule compliance...")
                analysis = analyze_conversation_logs("files/conversation_logs")
                
                if "error" not in analysis:
                    print(f"  Compliance rate: {analysis['summary']['compliance_rate']:.1%}")
                    print(f"  Violations found: {analysis['summary']['total_violations']}")
                    
                    if analysis['summary']['total_violations'] > 0:
                        print(f"  ⚠️  Run 'check-forget' for detailed violation analysis")
                    else:
                        print(f"  ✅ All conversations follow forget rules properly")

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
                cmd = ['pnpm', 'exec', 'tsx', 'scripts/convert-diagram.ts', str(input_path), str(output_path)]
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

            response = requests.post(f"{API_URL}/api/save", json={
                'diagram': diagram,
                'filename': filename,
                'format': format_type
            })
            response.raise_for_status()

            result = response.json()
            print(f"✓ {result.get('message', 'Saved to server')}")

        elif command == 'check-forget':
            log_dir = sys.argv[2] if len(sys.argv) > 2 else "conversation_logs"

            print(f"Analyzing forget rule compliance in {log_dir}...")
            analysis = analyze_conversation_logs(log_dir)

            if "error" in analysis:
                print(f"Error: {analysis['error']}")
                sys.exit(1)

            print(f"\n🔍 Forget Rule Analysis Report")
            print(f"  Total conversations: {analysis['total_conversations']}")
            print(f"  Compliance rate: {analysis['summary']['compliance_rate']:.1%}")
            print(f"  Total violations: {analysis['summary']['total_violations']}")
            print(f"  Total compliant: {analysis['summary']['total_compliant']}")

            if analysis['forget_rule_violations']:
                print(f"\n⚠️  Forget Rule Violations:")
                for violation in analysis['forget_rule_violations'][:5]:  # Show first 5
                    print(f"    {Path(violation['file']).name} (msg {violation['message_index']}): {violation['content_preview']}")

                if len(analysis['forget_rule_violations']) > 5:
                    print(f"    ... and {len(analysis['forget_rule_violations']) - 5} more")

            # Save detailed analysis
            Path('files/results').mkdir(exist_ok=True)
            analysis_file = 'files/results/forget_rule_analysis.json'
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"\n  Detailed analysis saved to: {analysis_file}")

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