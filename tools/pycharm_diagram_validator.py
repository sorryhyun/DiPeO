#!/usr/bin/env python3
"""Enhanced DiPeO Diagram Validator with PyCharm-friendly output"""

import json
import yaml
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import ast

class PyCharmDiagramValidator:
    """Validator that outputs in PyCharm's expected format for problem highlighting"""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath).absolute()
        self.base_dir = Path(os.environ.get('DIPEO_BASE_DIR', '.')).absolute()
        self.content_lines = []
        self.yaml_data = None
        
    def validate(self) -> int:
        """Run validation and output results in PyCharm format"""
        try:
            with open(self.filepath, 'r') as f:
                self.content_lines = f.readlines()
                f.seek(0)
                self.yaml_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            line = getattr(e, 'problem_mark', None)
            if line:
                self._output_error(line.line + 1, f"YAML syntax error: {e.problem}")
            else:
                self._output_error(1, f"YAML parsing failed: {e}")
            return 1
        except Exception as e:
            self._output_error(1, f"Failed to read file: {e}")
            return 1
            
        errors = 0
        
        # Check structure
        errors += self._check_required_fields()
        errors += self._check_start_end_nodes()
        errors += self._check_node_properties()
        errors += self._check_connections()
        errors += self._check_file_references()
        errors += self._check_inline_python()
        
        return errors
        
    def _find_line_number(self, search_text: str, start_line: int = 0) -> int:
        """Find line number containing specific text"""
        for i, line in enumerate(self.content_lines[start_line:], start=start_line):
            if search_text in line:
                return i + 1
        return 1
        
    def _output_error(self, line: int, message: str, column: int = 1):
        """Output error in PyCharm's expected format"""
        print(f"{self.filepath}:{line}:{column}: error: {message}")
        
    def _output_warning(self, line: int, message: str, column: int = 1):
        """Output warning in PyCharm's expected format"""
        print(f"{self.filepath}:{line}:{column}: warning: {message}")
        
    def _check_required_fields(self) -> int:
        """Check for required top-level fields"""
        errors = 0
        required = ['version', 'nodes', 'connections']
        
        for field in required:
            if field not in self.yaml_data:
                self._output_error(1, f"Missing required field '{field}'")
                errors += 1
                
        if self.yaml_data.get('version') != 'light':
            line = self._find_line_number('version:')
            self._output_error(line, f"Invalid version '{self.yaml_data.get('version')}', expected 'light'")
            errors += 1
            
        return errors
        
    def _check_start_end_nodes(self) -> int:
        """Ensure diagram has start and endpoint nodes"""
        errors = 0
        nodes = self.yaml_data.get('nodes', [])
        
        has_start = any(n.get('type') == 'start' for n in nodes)
        has_end = any(n.get('type') == 'endpoint' for n in nodes)
        
        if not has_start:
            line = self._find_line_number('nodes:')
            self._output_error(line, "Diagram must have a 'start' node")
            errors += 1
            
        if not has_end:
            line = self._find_line_number('nodes:')
            self._output_error(line, "Diagram must have an 'endpoint' node")
            errors += 1
            
        return errors
        
    def _check_node_properties(self) -> int:
        """Validate individual node properties"""
        errors = 0
        valid_types = {
            'start', 'endpoint', 'db', 'code_job', 'person_job', 'api_job',
            'condition', 'template_job', 'merge', 'select', 'iterator',
            'variable', 'formatter', 'saver', 'sub_diagram', 'hook',
            'user_response', 'json_schema_validator', 'notion',
            'typescript_ast', 'person_batch_job'
        }
        
        nodes = self.yaml_data.get('nodes', [])
        node_labels = set()
        
        for node in nodes:
            label = node.get('label', 'Unknown')
            
            # Find line number for this node
            node_line = self._find_line_number(f"label: {label}")
            
            # Check required fields
            for field in ['label', 'type', 'position']:
                if field not in node:
                    self._output_error(node_line, f"Node missing required field '{field}'")
                    errors += 1
                    
            # Check node type
            if node.get('type') not in valid_types:
                type_line = self._find_line_number(f"type: {node.get('type')}", node_line - 1)
                self._output_error(type_line, f"Invalid node type '{node.get('type')}'")
                errors += 1
                
            # Check duplicate labels
            if label in node_labels:
                self._output_error(node_line, f"Duplicate node label '{label}'")
                errors += 1
            node_labels.add(label)
            
        return errors
        
    def _check_connections(self) -> int:
        """Validate connections reference existing nodes"""
        errors = 0
        nodes = self.yaml_data.get('nodes', [])
        connections = self.yaml_data.get('connections', [])
        
        node_labels = {n.get('label') for n in nodes}
        
        for conn in connections:
            # Find connection line
            from_node = conn.get('from', '')
            to_node = conn.get('to', '')
            conn_line = self._find_line_number(f"from: {from_node}")
            
            if from_node not in node_labels:
                self._output_error(conn_line, f"Connection references unknown node '{from_node}'")
                errors += 1
                
            if to_node not in node_labels:
                to_line = self._find_line_number(f"to: {to_node}", conn_line - 1)
                self._output_error(to_line, f"Connection references unknown node '{to_node}'")
                errors += 1
                
        return errors
        
    def _check_file_references(self) -> int:
        """Check that referenced files exist"""
        errors = 0
        nodes = self.yaml_data.get('nodes', [])
        
        for node in nodes:
            props = node.get('props', {})
            label = node.get('label', 'Unknown')
            
            # Check file/filePath references
            for file_prop in ['file', 'filePath']:
                if file_prop in props:
                    filepath = props[file_prop]
                    full_path = self.base_dir / filepath
                    
                    if not full_path.exists():
                        # Find the line with this file reference
                        file_line = self._find_line_number(f"{file_prop}: {filepath}")
                        self._output_error(file_line, f"File not found: {filepath}")
                        errors += 1
                        
            # Check source_details for db write operations
            if node.get('type') == 'db' and props.get('operation') == 'write':
                if 'source_details' in props:
                    target_path = props['source_details']
                    # Just warn if target doesn't exist (it will be created)
                    target_line = self._find_line_number(f"source_details: {target_path}")
                    self._output_warning(target_line, f"Target file will be created: {target_path}")
                    
        return errors
        
    def _check_inline_python(self) -> int:
        """Validate inline Python code syntax"""
        errors = 0
        nodes = self.yaml_data.get('nodes', [])
        
        for node in nodes:
            if node.get('type') == 'code_job':
                props = node.get('props', {})
                if 'code' in props and 'filePath' not in props:
                    code = props['code']
                    label = node.get('label', 'Unknown')
                    
                    try:
                        ast.parse(code)
                    except SyntaxError as e:
                        # Find the start of the code block
                        code_line = self._find_line_number('code: |')
                        # Adjust for the syntax error line within the code block
                        error_line = code_line + (e.lineno or 1)
                        self._output_error(error_line, f"Python syntax error: {e.msg}")
                        errors += 1
                        
        return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: pycharm_diagram_validator.py <diagram_file>")
        sys.exit(1)
        
    validator = PyCharmDiagramValidator(sys.argv[1])
    errors = validator.validate()
    
    sys.exit(1 if errors > 0 else 0)


if __name__ == "__main__":
    main()