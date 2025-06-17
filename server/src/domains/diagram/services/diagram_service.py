import yaml
import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException

from ....shared.exceptions.exceptions import ValidationError
from ....services.llm_service import LLMService
from ....services.api_key_service import APIKeyService
from ....domains.person.memory.memory_service import MemoryService
from ....shared.utils.base_service import BaseService
from ....shared.utils.diagram_validator import DiagramValidator
from ..models.domain import DiagramID
from config import BASE_DIR

logger = logging.getLogger(__name__)


def round_position(position: dict) -> dict:
    """Round position coordinates to 1 decimal places."""
    return {
        "x": round(position["x"], 1),
        "y": round(position["y"], 1)
    }


class DiagramService(BaseService):
    """Service for handling diagram operations."""
    
    def __init__(self, llm_service: LLMService, api_key_service: APIKeyService, memory_service: MemoryService):
        super().__init__()
        self.llm_service = llm_service
        self.api_key_service = api_key_service
        self.memory_service = memory_service
        self.diagrams_dir = BASE_DIR / 'files' / 'diagrams'
        self.validator = DiagramValidator(api_key_service)


    def _validate_and_fix_api_keys(self, diagram: dict) -> None:
        """Validate and fix API keys in diagram persons."""
        valid_api_keys = {key["id"] for key in self.api_key_service.list_api_keys()}

        # Fix invalid API key references in persons
        persons = diagram.get("persons", {})
        # Only handle dict (Record format)
        if not isinstance(persons, dict):
            raise ValidationError("Persons must be a dictionary with person IDs as keys")
        
        for person in persons.values():
            if person.get("apiKeyId") and person["apiKeyId"] not in valid_api_keys:
                # Try to find a fallback key for the same service
                all_keys = self.api_key_service.list_api_keys()
                fallback = next(
                    (k for k in all_keys if k["service"] == person.get("service")),
                    None
                )
                if fallback:
                    logger.info(f"Replaced invalid apiKeyId {person['apiKeyId']} with {fallback['id']}")
                    person["apiKeyId"] = fallback["id"]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No valid API key found for service: {person.get('service')}"
                    )
    
    def _validate_diagram(self, diagram: dict) -> None:
        """Validate diagram structure."""
        self.validator.validate_or_raise(diagram, context="storage")
    
    def import_yaml(self, yaml_text: str) -> dict:
        """Import YAML agent definitions and convert to diagram state."""
        try:
            # Parse YAML content
            data = yaml.safe_load(yaml_text)
            
            # If the data is already in diagram format, validate and return it
            if isinstance(data, dict) and "nodes" in data and "arrows" in data:
                # Convert arrays to Record format if needed
                if isinstance(data.get("nodes"), list):
                    data["nodes"] = {n["id"]: n for n in data["nodes"]}
                if isinstance(data.get("arrows"), list):
                    data["arrows"] = {a["id"]: a for a in data["arrows"]}
                if isinstance(data.get("persons"), list):
                    data["persons"] = {p["id"]: p for p in data["persons"]}
                
                self._validate_diagram(data)
                # Ensure all required fields are present
                data.setdefault("persons", {})
                data.setdefault("apiKeys", {})
                data.setdefault("handles", {})
                return data
            
            # Otherwise, return an empty diagram structure
            # The frontend handles more complex YAML formats (LLM-friendly format)
            return {
                "nodes": {},
                "arrows": {},
                "handles": {},
                "persons": {},
                "apiKeys": {}
            }
            
        except yaml.YAMLError as e:
            raise ValidationError(f"Failed to parse YAML: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to import YAML: {e}")
    
    def export_llm_yaml(self, diagram: dict) -> str:
        """Export diagram to LLM-friendly YAML format.
        
        Note: This is a basic implementation. For sophisticated LLM YAML export,
        use the CLI tool which leverages the frontend TypeScript converters:
        `python tool.py convert example.json output.llm-yaml`
        """
        try:
            # Basic LLM-friendly format export
            nodes = diagram.get("nodes", {})
            arrows = diagram.get("arrows", {})
            persons = diagram.get("persons", {})
            
            # Only handle Record format
            if not isinstance(nodes, dict):
                raise ValidationError("Nodes must be a dictionary with node IDs as keys")
            if not isinstance(arrows, dict):
                raise ValidationError("Arrows must be a dictionary with arrow IDs as keys")
            if not isinstance(persons, dict):
                raise ValidationError("Persons must be a dictionary with person IDs as keys")
            
            node_list = list(nodes.values())
            arrow_list = list(arrows.values())
            person_list = list(persons.values())
            
            # Create simple flow representation
            flow = []
            for arrow in arrow_list:
                # Extract node ID from handle ID (format: "nodeId:handleName")
                source_node_id = arrow["source"].split(":")[0] if ":" in arrow["source"] else arrow["source"]
                target_node_id = arrow["target"].split(":")[0] if ":" in arrow["target"] else arrow["target"]
                source_node = nodes.get(source_node_id)
                target_node = nodes.get(target_node_id)
                
                if source_node and target_node:
                    source_label = source_node.get("data", {}).get("label", arrow["source"])
                    target_label = target_node.get("data", {}).get("label", arrow["target"])
                    variable = arrow.get("data", {}).get("label", "")
                    
                    if variable and variable != "flow":
                        flow.append(f'{source_label} -> {target_label}: "{variable}"')
                    else:
                        flow.append(f'{source_label} -> {target_label}')
            
            # Extract prompts from PersonJob nodes
            prompts = {}
            for node in node_list:
                if node.get("type") == "personJobNode":
                    data = node.get("data", {})
                    label = data.get("label", node["id"])
                    default_prompt = data.get("defaultPrompt", "")
                    if default_prompt:
                        prompts[label] = default_prompt
            
            # Extract agent configurations
            agents = {}
            for person in person_list:
                label = person.get("label", person["id"])
                config = {}
                if person.get("modelName") and person["modelName"] != "gpt-4":
                    config["model"] = person["modelName"]
                if person.get("service") and person["service"] != "openai":
                    config["service"] = person["service"]
                if person.get("systemPrompt"):
                    config["system"] = person["systemPrompt"]
                
                if config:
                    agents[label] = config
            
            # Build LLM YAML structure
            llm_yaml = {"flow": flow}
            if prompts:
                llm_yaml["prompts"] = prompts
            if agents:
                llm_yaml["agents"] = agents
            
            return yaml.dump(llm_yaml, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
        except Exception as e:
            raise ValidationError(f"Failed to export LLM YAML: {e}")
    
    def list_diagram_files(self, directory: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all diagram files in the diagrams directory.
        
        Returns a list of diagram metadata including:
        - id: filename without extension
        - name: human-readable name
        - path: relative path from diagrams directory
        - format: file format (yaml, json)
        - modified: last modification time
        - size: file size in bytes
        """
        diagrams = []
        
        # Determine which directory to scan
        if directory:
            scan_dir = self.diagrams_dir / directory
        else:
            scan_dir = self.diagrams_dir
            
        if not scan_dir.exists():
            return diagrams
        
        # Scan for diagram files
        for file_path in scan_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.yaml', '.yml', '.json']:
                try:
                    # Get file stats
                    stats = file_path.stat()
                    
                    # Create relative path from diagrams directory
                    relative_path = file_path.relative_to(self.diagrams_dir)
                    
                    # Determine format based on parent directory or filename
                    format_type = 'native'
                    if 'readable' in str(relative_path):
                        format_type = 'readable'
                    elif 'llm' in str(relative_path):
                        format_type = 'llm-readable'
                    elif relative_path.parent == Path('.'):
                        format_type = 'light'
                    
                    # Create diagram metadata
                    diagram_meta = {
                        'id': file_path.stem,  # filename without extension
                        'name': file_path.stem.replace('_', ' ').replace('-', ' ').title(),
                        'path': str(relative_path),
                        'format': format_type,
                        'extension': file_path.suffix[1:],  # Remove the dot
                        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        'size': stats.st_size
                    }
                    
                    diagrams.append(diagram_meta)
                    
                except Exception as e:
                    logger.warning(f"Failed to process diagram file {file_path}: {e}")
                    continue
        
        # Sort by modification time (newest first)
        diagrams.sort(key=lambda x: x['modified'], reverse=True)
        
        return diagrams
    
    def load_diagram(self, path: str) -> Dict[str, Any]:
        """Load a diagram from file.
        
        Args:
            path: Relative path from diagrams directory
            
        Returns:
            Diagram data in domain format
        """
        file_path = self.diagrams_dir / path
        
        if not file_path.exists():
            raise ValidationError(f"Diagram file not found: {path}")
        
        try:
            # Read file based on extension
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                raise ValidationError(f"Unsupported file format: {file_path.suffix}")
            
            # Convert to domain format if needed
            if isinstance(data, dict) and 'nodes' in data:
                # Already in diagram format, ensure it's in Record format
                if isinstance(data.get('nodes'), list):
                    data['nodes'] = {n['id']: n for n in data['nodes']}
                if isinstance(data.get('arrows'), list):
                    data['arrows'] = {a['id']: a for a in data['arrows']}
                if isinstance(data.get('persons'), list):
                    data['persons'] = {p['id']: p for p in data['persons']}
                if isinstance(data.get('handles'), list):
                    data['handles'] = {h['id']: h for h in data['handles']}
                if isinstance(data.get('apiKeys'), list):
                    data['apiKeys'] = {k['id']: k for k in data['apiKeys']}
                
                # Validate and fix API keys
                self._validate_and_fix_api_keys(data)
                
                # Ensure all required fields
                data.setdefault('nodes', {})
                data.setdefault('arrows', {})
                data.setdefault('handles', {})
                data.setdefault('persons', {})
                data.setdefault('apiKeys', {})
                
                return data
            else:
                # Not in expected format
                raise ValidationError("Invalid diagram format")
                
        except yaml.YAMLError as e:
            raise ValidationError(f"Failed to parse YAML file: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Failed to parse JSON file: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to load diagram: {e}")
    
    def save_diagram(self, path: str, diagram: Dict[str, Any]) -> None:
        """Save a diagram to file.
        
        Args:
            path: Relative path from diagrams directory
            diagram: Diagram data in domain format
        """
        file_path = self.diagrams_dir / path
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Validate diagram structure
            self._validate_diagram(diagram)
            
            # Save based on extension
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(diagram, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(diagram, f, indent=2, ensure_ascii=False)
            else:
                raise ValidationError(f"Unsupported file format: {file_path.suffix}")
                
            logger.info(f"Saved diagram to {path}")
            
        except Exception as e:
            raise ValidationError(f"Failed to save diagram: {e}")
    
    def create_diagram(self, name: str, diagram: Dict[str, Any], format: str = 'json') -> str:
        """Create a new diagram.
        
        Args:
            name: Name for the diagram (will be used as filename)
            diagram: Diagram data in domain format
            format: File format ('json' or 'yaml')
            
        Returns:
            Path to the created diagram
        """
        # Generate filename
        safe_name = name.replace(' ', '_').replace('/', '_')
        extension = '.yaml' if format == 'yaml' else '.json'
        path = f"{safe_name}{extension}"
        
        # Check if file already exists
        file_path = self.diagrams_dir / path
        if file_path.exists():
            # Generate unique name
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            path = f"{safe_name}_{unique_id}{extension}"
        
        # Save the diagram
        self.save_diagram(path, diagram)
        
        return path
    
    def update_diagram(self, path: str, diagram: Dict[str, Any]) -> None:
        """Update an existing diagram.
        
        Args:
            path: Relative path from diagrams directory
            diagram: Updated diagram data in domain format
        """
        file_path = self.diagrams_dir / path
        
        if not file_path.exists():
            raise ValidationError(f"Diagram file not found: {path}")
        
        # Save the updated diagram
        self.save_diagram(path, diagram)
    
    def delete_diagram(self, path: str) -> None:
        """Delete a diagram file.
        
        Args:
            path: Relative path from diagrams directory
        """
        file_path = self.diagrams_dir / path
        
        if not file_path.exists():
            raise ValidationError(f"Diagram file not found: {path}")
        
        try:
            file_path.unlink()
            logger.info(f"Deleted diagram at {path}")
        except Exception as e:
            raise ValidationError(f"Failed to delete diagram: {e}")
    
    async def save_diagram_with_id(self, diagram_dict: Dict[str, Any], filename: str) -> str:
        """Save a diagram with generated ID.
        
        Args:
            diagram_dict: Diagram data in dictionary format
            filename: Original filename for reference
            
        Returns:
            The diagram ID (which is the filename without extension)
        """
        # Special handling for quicksave
        if filename == 'quicksave.json':
            path = 'quicksave.json'
            diagram_id = 'quicksave'
            
            # Update metadata with ID
            if 'metadata' not in diagram_dict:
                diagram_dict['metadata'] = {}
            diagram_dict['metadata']['id'] = diagram_id
            
            # Save using existing method
            self.save_diagram(path, diagram_dict)
            return diagram_id
        
        # Extract name from metadata or use filename
        name = (diagram_dict.get('metadata', {}).get('name') or 
                Path(filename).stem)
        
        # Generate safe filename
        safe_name = name.replace(' ', '_').replace('/', '_')
        extension = '.yaml'  # Always save as YAML internally
        
        # Use ID from metadata if available, otherwise generate
        diagram_id = diagram_dict.get('metadata', {}).get('id')
        if diagram_id:
            # Use ID as filename
            path = f"{diagram_id}{extension}"
        else:
            # Generate unique filename
            import uuid
            unique_id = str(uuid.uuid4())
            path = f"{safe_name}_{unique_id}{extension}"
            diagram_id = Path(path).stem
            
            # Update metadata with ID
            if 'metadata' not in diagram_dict:
                diagram_dict['metadata'] = {}
            diagram_dict['metadata']['id'] = diagram_id
        
        # Save using existing method
        self.save_diagram(path, diagram_dict)
        
        return diagram_id
    
    async def get_diagram(self, diagram_id: DiagramID) -> Optional[Dict[str, Any]]:
        """Get a diagram by ID.
        
        Args:
            diagram_id: The diagram ID (filename without extension)
            
        Returns:
            Diagram dictionary or None if not found
        """
        # Try to find the diagram file
        for ext in ['.yaml', '.yml', '.json']:
            path = f"{diagram_id}{ext}"
            file_path = self.diagrams_dir / path
            if file_path.exists():
                try:
                    return self.load_diagram(path)
                except Exception as e:
                    logger.error(f"Failed to load diagram {path}: {e}")
                    continue
        
        # If not found by exact ID, search in all diagram files
        for file_info in self.list_diagram_files():
            try:
                diagram = self.load_diagram(file_info['path'])
                if diagram.get('metadata', {}).get('id') == diagram_id:
                    return diagram
            except Exception:
                continue
        
        return None
    
