"""
Stats command implementation for DiPeO CLI.
"""

from typing import List
from .utils import DiagramLoader


def stats_command(args: List[str]) -> None:
    """Execute stats command - shows diagram statistics"""
    if not args:
        print("Error: Missing input file")
        return
    
    try:
        diagram = DiagramLoader.load(args[0])
        
        # Calculate statistics
        nodes = diagram.get('nodes', {})
        node_types = {}
        for node_id, node in nodes.items():
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("\nDiagram Statistics:")
        print(f"  Persons: {len(diagram.get('persons', {}))}")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Arrows: {len(diagram.get('arrows', {}))}")
        print(f"  API Keys: {'Yes' if diagram.get('apiKeys') else 'No'}")
        
        if node_types:
            print("\nNode Types:")
            for node_type, count in sorted(node_types.items()):
                print(f"  {node_type}: {count}")
                
        # Show metadata if available
        metadata = diagram.get('metadata', {})
        if metadata:
            print("\nMetadata:")
            print(f"  Name: {metadata.get('name', 'Untitled')}")
            print(f"  Version: {metadata.get('version', 'Unknown')}")
            if metadata.get('description'):
                print(f"  Description: {metadata['description']}")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error reading diagram: {e}")