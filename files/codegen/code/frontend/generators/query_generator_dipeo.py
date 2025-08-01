"""Generate GraphQL queries following DiPeO's actual patterns."""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import specific query generators
from ..queries import (
    ApiKeysQueryGenerator,
    FilesQueryGenerator,
    FormatsQueryGenerator,
    NodesQueryGenerator,
    SystemQueryGenerator,
    PromptsQueryGenerator,
    ConversationsQueryGenerator,
    DiagramsQueryGenerator,
    PersonsQueryGenerator,
    ExecutionsQueryGenerator
)


class DiPeOQueryGenerator:
    """Generate GraphQL query files following DiPeO conventions."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    
    def write_query_file(self, entity: str, queries: List[str]):
        """Write queries to a GraphQL file."""
        filename = f"{entity}.graphql"
        filepath = self.output_dir / filename
        
        # Join queries with double newlines, but handle comments differently
        formatted_queries = []
        for i, query in enumerate(queries):
            if query.startswith('#'):
                # Comment - add extra newline before (except first)
                if i > 0:
                    formatted_queries.append("")
                formatted_queries.append(query)
            else:
                formatted_queries.append(query)
                # Add blank line after each query/mutation (except last)
                if i < len(queries) - 1 and not queries[i + 1].startswith('#'):
                    formatted_queries.append("")
        
        content = "\n".join(formatted_queries)
        
        with open(filepath, 'w') as f:
            f.write(content)
            f.write("\n")  # Ensure file ends with newline
        
        print(f"Generated {filepath}")
    
    def generate_all_queries(self):
        """Generate queries for all entities using modular generators."""
        # Use modular generators for all entities
        generators = {
            'diagrams': DiagramsQueryGenerator(),
            'persons': PersonsQueryGenerator(),
            'executions': ExecutionsQueryGenerator(),
            'apiKeys': ApiKeysQueryGenerator(),
            'files': FilesQueryGenerator(),
            'formats': FormatsQueryGenerator(),
            'nodes': NodesQueryGenerator(),
            'system': SystemQueryGenerator(),
            'prompts': PromptsQueryGenerator(),
            'conversations': ConversationsQueryGenerator()
        }
        
        # Generate queries for each entity
        for entity_name, generator in generators.items():
            queries = generator.generate()
            self.write_query_file(entity_name, queries)
        
        print(f"\nAll GraphQL queries generated successfully in {self.output_dir}")


def main():
    """Main entry point for query generation."""
    import sys
    
    # Default output directory for GraphQL queries
    output_dir = '/home/soryhyun/DiPeO/apps/web/src/__generated__/queries'
    
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    
    generator = DiPeOQueryGenerator(output_dir)
    generator.generate_all_queries()


if __name__ == "__main__":
    main()