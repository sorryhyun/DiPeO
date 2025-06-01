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


async def run_diagram_node_execution(diagram: Dict[str, Any]) -> Dict[str, Any]:
    """Execute diagram using Node.js execution runner (same logic as frontend)."""
    import subprocess
    import tempfile
    import os
    
    # Save diagram to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(diagram, f, indent=2)
        temp_diagram_path = f.name
    
    try:
        # Run Node.js execution runner
        runner_path = os.path.join(os.path.dirname(__file__), 'execution_runner.cjs')
        
        # Check if node-fetch is available, if not suggest installation
        try:
            subprocess.run(['node', '-e', 'require("node-fetch")'], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("⚠️  Missing node-fetch dependency. Install with: npm install node-fetch")
            print("   Falling back to backend execution...")
            return await run_diagram_backend_fallback(diagram)
        
        result = subprocess.run(
            ['node', runner_path, temp_diagram_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            print(f"Node.js execution failed: {result.stderr}")
            print("Falling back to backend execution...")
            return await run_diagram_backend_fallback(diagram)
        
        # Parse results from the saved file
        results_path = 'results.json'
        if os.path.exists(results_path):
            with open(results_path, 'r') as f:
                return json.load(f)
        else:
            return {
                "context": {},
                "total_cost": 0,
                "messages": []
            }
            
    except subprocess.TimeoutExpired:
        print("Execution timeout exceeded")
        return {
            "context": {},
            "total_cost": 0,
            "messages": [],
            "error": "Execution timeout"
        }
    except Exception as e:
        print(f"Execution error: {e}")
        return await run_diagram_backend_fallback(diagram)
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_diagram_path)
        except:
            pass


async def run_diagram_backend_fallback(diagram: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback to direct backend execution (simplified)."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"{API_URL}/api/run-diagram",
                json=diagram,
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
                return {
                    "context": {},
                    "total_cost": 0,
                    "messages": [],
                    "error": f"Backend execution failed: {response.status}"
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


def run_diagram(diagram: Dict[str, Any], show_in_browser: bool = True, pre_initialize: bool = True) -> Dict[str, Any]:
    """Synchronous wrapper for execution with optional pre-initialization."""
    if pre_initialize:
        print("🔧 Pre-initializing models...")
        pre_initialize_models(diagram)
        print()
    
    return asyncio.run(run_diagram_node_execution(diagram))


def open_browser_monitor():
    """Open browser to monitoring page."""
    import webbrowser
    monitor_url = "http://localhost:3000/?monitor=true"
    print(f"🌐 Opening browser monitor at {monitor_url}")
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


def pre_initialize_models(diagram: Dict[str, Any]) -> Dict[str, Any]:
    """Pre-initialize all models used in the diagram."""
    person_models = extract_person_models(diagram)
    
    if not person_models:
        return {"message": "No person nodes with complete model configuration found", "initialized": 0}
    
    print(f"🔧 Pre-initializing {len(person_models)} unique model(s)...")
    
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
                    print(f"  ✅ {config['service']}:{config['model']} (person: {config['person_id']})")
                    results["initialized"] += 1
                    results["details"].append({
                        "status": "success", 
                        "config": config,
                        "message": data.get('message', '')
                    })
                else:
                    print(f"  ❌ {config['service']}:{config['model']} - {data.get('error', 'Unknown error')}")
                    results["failed"] += 1
                    results["details"].append({
                        "status": "failed",
                        "config": config, 
                        "error": data.get('error', 'Unknown error')
                    })
            else:
                print(f"  ❌ {config['service']}:{config['model']} - HTTP {response.status_code}")
                results["failed"] += 1
                results["details"].append({
                    "status": "failed",
                    "config": config,
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"  ❌ {config['service']}:{config['model']} - {str(e)}")
            results["failed"] += 1
            results["details"].append({
                "status": "failed",
                "config": config,
                "error": str(e)
            })
    
    if results["initialized"] > 0:
        print(f"✓ Successfully pre-initialized {results['initialized']} model(s)")
    if results["failed"] > 0:
        print(f"⚠️  Failed to pre-initialize {results['failed']} model(s)")
    
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
        print("  run-and-monitor <file>                    - 🚀 RECOMMENDED: Pre-load models, open browser, then run diagram")
        print("  run <file> [--no-browser] [--no-preload]  - Run diagram (with browser visualization by default)")
        print("  run-headless <file>                       - Run diagram without browser visualization")
        print("  monitor                                   - Open browser monitoring page")
        print("  preload <file>                            - Pre-initialize all models in diagram")
        print("  convert <input> <output>                  - Convert between formats (JSON/YAML/UML)")
        print("  stats <file>                              - Show diagram statistics")
        print("  server-save <file> <name>                 - Save diagram to server")
        print("  check-forget [log_dir]                    - Analyze forget rule compliance")
        print("  run-and-check <file> [output]             - Run diagram and check forget rules")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == 'monitor':
            open_browser_monitor()
            print("Browser monitor opened. Run diagrams with 'run' command to see them visualized.")

        elif command == 'run-and-monitor':
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            print(f"Loading diagram from {sys.argv[2]}...")
            diagram = load_diagram(sys.argv[2])

            # Pre-load models first
            print("🔧 Pre-initializing models for faster execution...")
            pre_initialize_models(diagram)

            # Open browser
            print("\n🌐 Opening browser monitor...")
            open_browser_monitor()

            # Wait a bit for browser to connect
            print("Waiting for browser to connect...")
            time.sleep(2)

            # Then run the diagram (skip pre-initialization since we already did it)
            print("🚀 Running diagram with browser visualization...")
            result = run_diagram(diagram, show_in_browser=True, pre_initialize=False)

            print(f"\n✓ Execution complete!")
            print(f"  Total cost: ${result.get('total_cost', 0):.4f}")
            if 'context' in result:
                print(f"  Context keys: {list(result['context'].keys())}")

        elif command == 'preload':
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            print(f"Loading diagram from {sys.argv[2]}...")
            diagram = load_diagram(sys.argv[2])

            results = pre_initialize_models(diagram)
            
            if results["initialized"] == 0 and results["failed"] == 0:
                print("ℹ️  No person nodes with complete model configuration found")
            else:
                print(f"\n📊 Pre-initialization Summary:")
                print(f"  ✅ Successful: {results['initialized']}")
                print(f"  ❌ Failed: {results['failed']}")

        elif command == 'run':
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            # Check for flags
            show_in_browser = '--no-browser' not in sys.argv
            pre_initialize = '--no-preload' not in sys.argv

            print(f"Loading diagram from {sys.argv[2]}...")
            diagram = load_diagram(sys.argv[2])

            if show_in_browser:
                print("🌐 Running diagram (browser visualization enabled)")
                print("   Open http://localhost:3000 in your browser to see the execution")
            else:
                print("Running diagram (browser visualization disabled)")

            result = run_diagram(diagram, show_in_browser=show_in_browser, pre_initialize=pre_initialize)

            # Save results
            output_file = 'results.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  Results saved to: {output_file}")

        elif command == 'run-headless':
            # Use the streaming endpoint but without browser visualization
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            print(f"Loading diagram from {sys.argv[2]}...")
            diagram = load_diagram(sys.argv[2])

            print("Running diagram (headless)...")
            result = run_diagram(diagram, show_in_browser=False, pre_initialize=True)

            print(f"\n✓ Execution complete")
            print(f"  Total cost: ${result.get('total_cost', 0):.4f}")
            
            # Save results
            output_file = 'results.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  Results saved to: {output_file}")

        elif command == 'convert':
            if len(sys.argv) < 4:
                print("Error: Usage: convert <input> <output>")
                sys.exit(1)

            input_path = Path(sys.argv[2])
            output_path = Path(sys.argv[3])

            # Load input
            if input_path.suffix in ['.puml', '.uml']:
                print(f"Importing UML from {input_path}...")
                diagram = import_uml(str(input_path))
            else:
                print(f"Loading diagram from {input_path}...")
                diagram = load_diagram(str(input_path))

            # Save output
            if output_path.suffix in ['.puml', '.uml']:
                print(f"Exporting to UML...")
                uml_content = export_uml(diagram)
                with open(output_path, 'w') as f:
                    f.write(uml_content)
            else:
                print(f"Saving to {output_path}...")
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
            analysis_file = 'apps/tools/forget_rule_analysis.json'
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"\n  Detailed analysis saved to: {analysis_file}")

        elif command == 'run-and-check':
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            print(f"Loading diagram from {sys.argv[2]}...")
            diagram = load_diagram(sys.argv[2])

            print("Running diagram...")
            result = run_diagram(diagram, show_in_browser=False, pre_initialize=True)

            print(f"\n✓ Execution complete")
            print(f"  Total cost: ${result.get('total_cost', 0):.4f}")

            if 'context' in result:
                print(f"  Context keys: {list(result['context'].keys())}")

            # Save results
            output_file = sys.argv[3] if len(sys.argv) > 3 else 'results.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  Results saved to: {output_file}")

            # Now check forget rules in conversation logs
            print(f"\n🔍 Checking forget rule compliance...")
            analysis = analyze_conversation_logs("conversation_logs")

            if "error" not in analysis:
                print(f"  Compliance rate: {analysis['summary']['compliance_rate']:.1%}")
                print(f"  Violations found: {analysis['summary']['total_violations']}")

                if analysis['summary']['total_violations'] > 0:
                    print(f"  ⚠️  Run 'check-forget' for detailed violation analysis")
                else:
                    print(f"  ✅ All conversations follow forget rules properly")

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