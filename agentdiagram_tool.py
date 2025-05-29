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


async def run_diagram_streaming(diagram: Dict[str, Any], show_in_browser: bool = True) -> Dict[str, Any]:
    """Execute diagram with streaming support for browser visualization."""

    # Use the external endpoint that broadcasts to browsers
    endpoint = "/api/external/run-diagram" if show_in_browser else "/api/run-diagram"

    async with aiohttp.ClientSession() as session:
        async with session.post(
                f"{API_URL}{endpoint}",
                json=diagram,
                headers={"Content-Type": "application/json"}
        ) as response:
            result = {
                "context": {},
                "total_cost": 0,
                "messages": []
            }

            # Process streaming response
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])

                        # Print progress to console
                        if data['type'] == 'node_start':
                            print(f"  ▶️  Starting node: {data['nodeId']}")
                        elif data['type'] == 'node_complete':
                            print(f"  ✅ Completed node: {data['nodeId']}")
                            if data.get('output_preview'):
                                print(f"     Output: {data['output_preview'][:50]}...")
                        elif data['type'] == 'execution_complete':
                            result['context'] = data.get('context', {})
                            result['total_cost'] = data.get('total_cost', 0)
                            print(f"\n✓ Execution complete")
                        elif data['type'] == 'execution_error':
                            print(f"  ❌ Error: {data.get('error', 'Unknown error')}")
                            raise Exception(data.get('error', 'Execution failed'))
                        elif data['type'] == 'message_added':
                            result['messages'].append(data.get('message'))

                    except json.JSONDecodeError:
                        continue

            return result


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


def run_diagram(diagram: Dict[str, Any], show_in_browser: bool = True) -> Dict[str, Any]:
    """Synchronous wrapper for streaming execution."""
    return asyncio.run(run_diagram_streaming(diagram, show_in_browser))


def open_browser_monitor():
    """Open browser to monitoring page."""
    import webbrowser
    monitor_url = "http://localhost:5173/?monitor=true"
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
                person_id = message.get("sender_person_id") or message.get("person_id")
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
        print("Usage: python agentdiagram_tool.py <command> [options]\n")
        print("Commands:")
        print("  run <file> [--no-browser]     - Run diagram (with browser visualization by default)")
        print("  run-headless <file>           - Run diagram without browser visualization")
        print("  monitor                       - Open browser monitoring page")
        print("  run-and-monitor <file>        - Open browser then run diagram")
        # ... other commands ...
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

            # Open browser first
            open_browser_monitor()

            # Wait a bit for browser to connect
            print("Waiting for browser to connect...")
            time.sleep(2)

            # Then run the diagram
            print(f"\nLoading diagram from {sys.argv[2]}...")
            diagram = load_diagram(sys.argv[2])

            print("Running diagram with browser visualization...")
            result = run_diagram(diagram, show_in_browser=True)

            print(f"  Total cost: ${result.get('total_cost', 0):.4f}")
            if 'context' in result:
                print(f"  Context keys: {list(result['context'].keys())}")

        elif command == 'run':
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            # Check for --no-browser flag
            show_in_browser = '--no-browser' not in sys.argv

            print(f"Loading diagram from {sys.argv[2]}...")
            diagram = load_diagram(sys.argv[2])

            if show_in_browser:
                print("🌐 Running diagram (browser visualization enabled)")
                print("   Open http://localhost:5173 in your browser to see the execution")
            else:
                print("Running diagram (browser visualization disabled)")

            result = run_diagram(diagram, show_in_browser=show_in_browser)

            # Save results
            output_file = 'results.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  Results saved to: {output_file}")

        elif command == 'run-headless':
            # Original sync execution without browser
            if len(sys.argv) < 3:
                print("Error: Missing input file")
                sys.exit(1)

            print(f"Loading diagram from {sys.argv[2]}...")
            diagram = load_diagram(sys.argv[2])

            print("Running diagram (headless)...")
            response = requests.post(f"{API_URL}/api/run-diagram-sync", json=diagram)
            response.raise_for_status()
            result = response.json()

            print(f"\n✓ Execution complete")
            print(f"  Total cost: ${result.get('total_cost', 0):.4f}")

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
            result = run_diagram(diagram)

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