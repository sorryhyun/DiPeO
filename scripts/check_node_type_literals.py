#!/usr/bin/env python3
"""Check for string literal usage in node type comparisons.

This script ensures that all node type comparisons use the NodeType enum
instead of string literals, promoting type safety and preventing typos.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple

# Node type string literals to check for
NODE_TYPE_LITERALS = {
    "start", "person_job", "person_batch_job", "condition", 
    "db", "endpoint", "user_response", "code_job", "api_job", 
    "hook", "notion"
}

# Handle label string literals to check for
HANDLE_LABEL_LITERALS = {
    "default", "first", "condtrue", "condfalse"
}


class StringLiteralChecker(ast.NodeVisitor):
    """AST visitor to find string literal comparisons."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[Tuple[int, int, str, str]] = []
        
    def visit_Compare(self, node: ast.Compare) -> None:
        """Check comparison operations for string literals."""
        # Check left side
        if isinstance(node.left, ast.Attribute):
            attr_name = node.left.attr
            
            # Check for node.type == "literal" or similar
            if attr_name in ("type", "node_type"):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                        if comparator.value in NODE_TYPE_LITERALS:
                            self.violations.append((
                                node.lineno,
                                node.col_offset,
                                f'node.type == "{comparator.value}"',
                                f'node.type == NodeType.{comparator.value}.value'
                            ))
            
            # Check for handle comparisons
            elif attr_name in ("handle", "handle_label", "target_handle", "source_handle"):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                        if comparator.value in HANDLE_LABEL_LITERALS:
                            self.violations.append((
                                node.lineno,
                                node.col_offset,
                                f'{attr_name} == "{comparator.value}"',
                                f'{attr_name} == HandleLabel.{comparator.value}.value'
                            ))
        
        # Continue visiting child nodes
        self.generic_visit(node)
        
    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Check dictionary access with string literals."""
        # Check for patterns like data["type"] == "person_job"
        if isinstance(node.slice, ast.Constant) and node.slice.value == "type":
            parent = getattr(node, '_parent', None)
            if isinstance(parent, ast.Compare):
                for comparator in parent.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                        if comparator.value in NODE_TYPE_LITERALS:
                            self.violations.append((
                                parent.lineno,
                                parent.col_offset,
                                f'data["type"] == "{comparator.value}"',
                                f'data["type"] == NodeType.{comparator.value}.value'
                            ))
        
        self.generic_visit(node)


def check_file(filepath: Path) -> List[Tuple[str, int, int, str, str]]:
    """Check a single Python file for string literal violations."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content, filename=str(filepath))
        
        # Add parent references for better context
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child._parent = node
                
        checker = StringLiteralChecker(str(filepath))
        checker.visit(tree)
        
        return [(str(filepath), *v) for v in checker.violations]
        
    except Exception as e:
        print(f"Error checking {filepath}: {e}", file=sys.stderr)
        return []


def main():
    """Main entry point."""
    # Find all Python files in the project
    root_dir = Path(__file__).parent.parent
    python_files = []
    
    # Add all Python source directories
    for pattern in ["dipeo/**/*.py", "apps/*/src/**/*.py"]:
        python_files.extend(root_dir.glob(pattern))
    
    # Exclude generated files
    python_files = [
        f for f in python_files 
        if "models.py" not in f.name and "conversions.py" not in f.name
    ]
    
    all_violations = []
    for filepath in python_files:
        violations = check_file(filepath)
        all_violations.extend(violations)
    
    if all_violations:
        print("Found string literal violations:\n")
        for filename, line, col, found, expected in all_violations:
            print(f"{filename}:{line}:{col}")
            print(f"  Found:    {found}")
            print(f"  Expected: {expected}")
            print()
        
        print(f"\nTotal violations: {len(all_violations)}")
        print("\nTo fix these violations, import and use the appropriate enums:")
        print("  from dipeo.models import NodeType, HandleLabel")
        sys.exit(1)
    else:
        print("✓ No string literal violations found!")
        sys.exit(0)


if __name__ == "__main__":
    main()