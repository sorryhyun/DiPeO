#!/usr/bin/env python3
"""
DiPeO CLI Tool v2 - Using Deterministic State Machine Executor
A reliable command-line interface for DiPeO diagram operations
"""

import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
from datetime import datetime
import logging

# Add the apps directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from apps.cli.deterministic_executor import DeterministicExecutor, ExecutionContext, ExecutionState


# Configure logging
def setup_logging(debug: bool = False):
    """Configure logging based on debug mode"""
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' if debug else '%(message)s'
    logging.basicConfig(level=level, format=format_str)


class CLIFormatter:
    """Formats execution results for CLI output"""
    
    @staticmethod
    def format_result(ctx: ExecutionContext) -> str:
        """Format execution result for display"""
        lines = []
        
        # Header
        lines.append("\n" + "="*60)
        lines.append(f"Execution ID: {ctx.execution_id}")
        lines.append(f"Status: {ctx.state.value.upper()}")
        
        # Duration
        if ctx.end_time:
            duration = ctx.end_time - ctx.start_time
            lines.append(f"Duration: {duration:.2f} seconds")
        
        # Error if any
        if ctx.error:
            lines.append(f"\nError: {ctx.error}")
        
        # Summary
        lines.append(f"\nProcessed {len(ctx.events)} events")
        lines.append(f"Completed {len(ctx.node_outputs)} nodes")
        
        # Token usage
        total_tokens = sum(
            event.get('token_count', 0) 
            for event in ctx.events 
            if event.get('type') == 'node_complete'
        )
        if total_tokens > 0:
            lines.append(f"Total tokens: {total_tokens:,}")
        
        lines.append("="*60 + "\n")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_node_outputs(ctx: ExecutionContext) -> str:
        """Format node outputs for display"""
        if not ctx.node_outputs:
            return "No outputs generated."
        
        lines = ["\nNode Outputs:"]
        lines.append("-" * 40)
        
        for node_id, output in ctx.node_outputs.items():
            lines.append(f"\n{node_id}:")
            if isinstance(output, dict):
                lines.append(json.dumps(output, indent=2))
            else:
                lines.append(str(output))
        
        return '\n'.join(lines)


class DiPeOCLI:
    """Main CLI application"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description='DiPeO CLI - Execute agent diagrams',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run a diagram
  python tool_v2.py run diagram.json
  
  # Run with debug output
  python tool_v2.py run diagram.json --debug
  
  # Run with custom timeout
  python tool_v2.py run diagram.json --timeout 600
  
  # Monitor execution (stream events)
  python tool_v2.py run diagram.json --monitor
  
  # Save outputs to file
  python tool_v2.py run diagram.json --output results.json
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Commands')
        
        # Run command
        run_parser = subparsers.add_parser('run', help='Execute a diagram')
        run_parser.add_argument('diagram', help='Path to diagram file (JSON/YAML)')
        run_parser.add_argument('--debug', action='store_true', help='Enable debug output')
        run_parser.add_argument('--monitor', action='store_true', help='Monitor mode (stream events)')
        run_parser.add_argument('--timeout', type=int, default=300, help='Execution timeout in seconds')
        run_parser.add_argument('--output', help='Save outputs to file')
        run_parser.add_argument('--ws-url', default='ws://localhost:8000/api/ws', help='WebSocket URL')
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show diagram statistics')
        stats_parser.add_argument('diagram', help='Path to diagram file')
        
        # Convert command (kept for compatibility)
        convert_parser = subparsers.add_parser('convert', help='Convert between formats')
        convert_parser.add_argument('input', help='Input file')
        convert_parser.add_argument('output', help='Output file')
        
        return parser
    
    async def run_command(self, args) -> int:
        """Execute the run command"""
        setup_logging(args.debug)
        
        # Create executor
        executor = DeterministicExecutor(
            ws_url=args.ws_url,
            monitor_mode=args.monitor,
            debug=args.debug,
            timeout=args.timeout
        )
        
        try:
            # Execute diagram
            print(f"🚀 Executing diagram: {args.diagram}")
            ctx = await executor.execute(args.diagram)
            
            # Display results
            print(CLIFormatter.format_result(ctx))
            
            # Show outputs if not in monitor mode
            if not args.monitor and ctx.node_outputs:
                print(CLIFormatter.format_node_outputs(ctx))
            
            # Save outputs if requested
            if args.output and ctx.node_outputs:
                with open(args.output, 'w') as f:
                    json.dump({
                        'execution_id': ctx.execution_id,
                        'status': ctx.state.value,
                        'outputs': ctx.node_outputs,
                        'duration': ctx.end_time - ctx.start_time if ctx.end_time else None,
                        'events': len(ctx.events),
                        'timestamp': datetime.now().isoformat()
                    }, f, indent=2)
                print(f"\n💾 Outputs saved to: {args.output}")
            
            # Return appropriate exit code
            if ctx.state == ExecutionState.COMPLETED:
                return 0
            elif ctx.state == ExecutionState.ABORTED:
                return 130  # Standard exit code for SIGINT
            else:
                return 1
                
        except FileNotFoundError:
            print(f"❌ Error: Diagram file not found: {args.diagram}")
            return 1
        except KeyboardInterrupt:
            print("\n⚠️  Execution interrupted by user")
            return 130
        except Exception as e:
            print(f"❌ Error: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            return 1
    
    def stats_command(self, args) -> int:
        """Show diagram statistics"""
        try:
            # Load diagram
            import yaml
            path = Path(args.diagram)
            
            with open(path, 'r') as f:
                if path.suffix in ['.yaml', '.yml']:
                    diagram = yaml.safe_load(f)
                else:
                    diagram = json.load(f)
            
            # Calculate stats
            nodes = diagram.get('nodes', {})
            arrows = diagram.get('arrows', {})
            persons = diagram.get('persons', {})
            
            # Count node types
            node_types = {}
            for node in nodes.values():
                node_type = node.get('type') or node.get('data', {}).get('type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            # Display stats
            print(f"\nDiagram Statistics: {args.diagram}")
            print("="*50)
            print(f"Total nodes: {len(nodes)}")
            print(f"Total connections: {len(arrows)}")
            print(f"Total persons: {len(persons)}")
            print("\nNode types:")
            for node_type, count in sorted(node_types.items()):
                print(f"  {node_type}: {count}")
            
            # Check for potential issues
            print("\nValidation:")
            start_nodes = sum(1 for n in nodes.values() 
                            if n.get('type') == 'start' or n.get('data', {}).get('type') == 'start')
            if start_nodes == 0:
                print("  ⚠️  No start node found")
            elif start_nodes > 1:
                print(f"  ⚠️  Multiple start nodes found ({start_nodes})")
            else:
                print("  ✓ Valid start node configuration")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    def convert_command(self, args) -> int:
        """Convert between formats"""
        try:
            import yaml
            
            # Load input
            input_path = Path(args.input)
            with open(input_path, 'r') as f:
                if input_path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # Save output
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                if output_path.suffix in ['.yaml', '.yml']:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
                else:
                    json.dump(data, f, indent=2)
            
            print(f"✓ Converted {args.input} to {args.output}")
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    async def main(self) -> int:
        """Main entry point"""
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return 1
        
        if args.command == 'run':
            return await self.run_command(args)
        elif args.command == 'stats':
            return self.stats_command(args)
        elif args.command == 'convert':
            return self.convert_command(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1


def main():
    """Entry point for the CLI"""
    cli = DiPeOCLI()
    exit_code = asyncio.run(cli.main())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()