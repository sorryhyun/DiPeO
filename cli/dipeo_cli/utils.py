"""
Utility functions for the DiPeO CLI.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .models import DomainDiagram


DEFAULT_API_KEY = "APIKEY_387B73"


class DiagramValidator:
    """Validates diagram structure using local models"""
    
    @staticmethod
    def validate_diagram(diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Validate diagram using local DomainDiagram model"""
        try:
            # Ensure all required fields exist with proper defaults
            if 'nodes' not in diagram:
                diagram['nodes'] = {}
            if 'arrows' not in diagram:
                diagram['arrows'] = {}
            if 'handles' not in diagram:
                diagram['handles'] = {}
            if 'persons' not in diagram:
                diagram['persons'] = {}
            if 'apiKeys' not in diagram:
                diagram['apiKeys'] = {}
            
            # Add default API key if needed
            if not diagram['apiKeys'] and diagram['persons']:
                diagram['apiKeys'][DEFAULT_API_KEY] = {
                    'id': DEFAULT_API_KEY,
                    'label': 'Default API Key',
                    'service': 'openai',
                    'key': 'test-key'
                }
            
            # Add metadata if missing
            if 'metadata' not in diagram:
                diagram['metadata'] = {
                    'name': 'CLI Diagram',
                    'created': datetime.now().isoformat(),
                    'modified': datetime.now().isoformat(),
                    'version': '2.0.0'
                }
            
            # Convert apiKeys to api_keys for model
            if 'apiKeys' in diagram:
                diagram['api_keys'] = diagram.pop('apiKeys')
            
            # Validate using local model
            domain_diagram = DomainDiagram(**diagram)
            domain_diagram.validate()
            
            # Convert back to dict format
            validated = domain_diagram.model_dump()
            
            # Convert api_keys back to apiKeys for backward compatibility
            if 'api_keys' in validated:
                validated['apiKeys'] = validated.pop('api_keys')
            
            return validated
            
        except Exception as e:
            print(f"⚠️  Validation warning: {str(e)}")
            # Return original diagram with defaults applied
            return diagram


class DiagramLoader:
    """Handles loading and saving diagrams"""
    
    @staticmethod
    def load(file_path: str) -> Dict[str, Any]:
        """Load diagram from JSON or YAML file"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Diagram file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                diagram = yaml.safe_load(f)
            else:
                diagram = json.load(f)
        
        return DiagramValidator.validate_diagram(diagram)
    
    @staticmethod
    def save(diagram: Dict[str, Any], file_path: str) -> None:
        """Save diagram to JSON or YAML file"""
        path = Path(file_path)
        
        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            if path.suffix in ['.yaml', '.yml']:
                yaml.dump(diagram, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(diagram, f, indent=2)