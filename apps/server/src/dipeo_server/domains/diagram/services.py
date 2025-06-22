import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dipeo_domain import DiagramID
from fastapi import HTTPException

from config import BASE_DIR
from dipeo_server.core import APIKeyService, BaseService, ValidationError
from dipeo_server.domains.llm import LLMServiceClass as LLMService
from dipeo_server.domains.person import SimplifiedMemoryService as MemoryService

from .validators import DiagramValidator

logger = logging.getLogger(__name__)


def round_position(position: dict) -> dict:
    return {"x": round(position["x"], 1), "y": round(position["y"], 1)}


class DiagramService(BaseService):
    """Service for handling diagram operations."""

    def __init__(
        self,
        llm_service: LLMService,
        api_key_service: APIKeyService,
        memory_service: MemoryService,
    ):
        super().__init__()
        self.llm_service = llm_service
        self.api_key_service = api_key_service
        self.memory_service = memory_service
        self.diagrams_dir = BASE_DIR / "files" / "diagrams"
        self.validator = DiagramValidator(api_key_service)

    def _validate_and_fix_api_keys(self, diagram: dict) -> None:
        valid_api_keys = {key["id"] for key in self.api_key_service.list_api_keys()}

        # Fix invalid API key references in persons
        persons = diagram.get("persons", {})
        # Only handle dict (Record format)
        if not isinstance(persons, dict):
            raise ValidationError(
                "Persons must be a dictionary with person IDs as keys"
            )

        for person in persons.values():
            if person.get("apiKeyId") and person["apiKeyId"] not in valid_api_keys:
                # Try to find a fallback key for the same service
                all_keys = self.api_key_service.list_api_keys()
                fallback = next(
                    (k for k in all_keys if k["service"] == person.get("service")), None
                )
                if fallback:
                    logger.info(
                        f"Replaced invalid apiKeyId {person['apiKeyId']} with {fallback['id']}"
                    )
                    person["apiKeyId"] = fallback["id"]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No valid API key found for service: {person.get('service')}",
                    )

    def _validate_diagram(self, diagram: dict) -> None:
        """Validate diagram structure."""
        self.validator.validate_or_raise(diagram, context="storage")

    def convert_from_yaml(self, yaml_text: str) -> dict:
        """Convert YAML content to diagram state."""
        try:
            data = yaml.safe_load(yaml_text)

            if isinstance(data, dict) and "nodes" in data and "arrows" in data:
                if isinstance(data.get("nodes"), list):
                    data["nodes"] = {n["id"]: n for n in data["nodes"]}
                if isinstance(data.get("arrows"), list):
                    data["arrows"] = {a["id"]: a for a in data["arrows"]}
                if isinstance(data.get("persons"), list):
                    data["persons"] = {p["id"]: p for p in data["persons"]}

                self._validate_diagram(data)
                data.setdefault("persons", {})
                data.setdefault("api_keys", {})
                data.setdefault("handles", {})
                return data

            # Frontend handles more complex YAML formats
            return {
                "nodes": {},
                "arrows": {},
                "handles": {},
                "persons": {},
                "api_keys": {},
            }

        except yaml.YAMLError as e:
            raise ValidationError(f"Failed to parse YAML: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to import YAML: {e}")

    def convert_to_llm_yaml(self, diagram: dict) -> str:
        """Convert diagram to LLM-friendly YAML format.

        Note: This is a basic implementation. For sophisticated LLM YAML export,
        use the CLI tool which leverages the frontend TypeScript converters:
        `dipeo convert example.json output.llm-yaml`
        """
        try:
            nodes = diagram.get("nodes", {})
            arrows = diagram.get("arrows", {})
            persons = diagram.get("persons", {})

            if not isinstance(nodes, dict):
                raise ValidationError(
                    "Nodes must be a dictionary with node IDs as keys"
                )
            if not isinstance(arrows, dict):
                raise ValidationError(
                    "Arrows must be a dictionary with arrow IDs as keys"
                )
            if not isinstance(persons, dict):
                raise ValidationError(
                    "Persons must be a dictionary with person IDs as keys"
                )

            node_list = list(nodes.values())
            arrow_list = list(arrows.values())
            person_list = list(persons.values())

            flow = []
            for arrow in arrow_list:
                source_node_id = (
                    arrow["source"].split(":")[0]
                    if ":" in arrow["source"]
                    else arrow["source"]
                )
                target_node_id = (
                    arrow["target"].split(":")[0]
                    if ":" in arrow["target"]
                    else arrow["target"]
                )
                source_node = nodes.get(source_node_id)
                target_node = nodes.get(target_node_id)

                if source_node and target_node:
                    source_label = source_node.get("data", {}).get(
                        "label", arrow["source"]
                    )
                    target_label = target_node.get("data", {}).get(
                        "label", arrow["target"]
                    )
                    variable = arrow.get("data", {}).get("label", "")

                    if variable and variable != "flow":
                        flow.append(f'{source_label} -> {target_label}: "{variable}"')
                    else:
                        flow.append(f"{source_label} -> {target_label}")

            prompts = {}
            for node in node_list:
                if node.get("type") == "personJobNode":
                    data = node.get("data", {})
                    label = data.get("label", node["id"])
                    default_prompt = data.get("defaultPrompt", "")
                    if default_prompt:
                        prompts[label] = default_prompt

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

            llm_yaml = {"flow": flow}
            if prompts:
                llm_yaml["prompts"] = prompts
            if agents:
                llm_yaml["agents"] = agents

            return yaml.dump(
                llm_yaml, default_flow_style=False, sort_keys=False, allow_unicode=True
            )

        except Exception as e:
            raise ValidationError(f"Failed to export LLM YAML: {e}")

    def list_diagram_files(
        self, directory: Optional[str] = None
    ) -> List[Dict[str, Any]]:
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

        if directory:
            scan_dir = self.diagrams_dir / directory
        else:
            scan_dir = self.diagrams_dir

        if not scan_dir.exists():
            return diagrams

        for file_path in scan_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [
                ".yaml",
                ".yml",
                ".json",
            ]:
                try:
                    stats = file_path.stat()

                    relative_path = file_path.relative_to(self.diagrams_dir)

                    format_type = "native"
                    if "readable" in str(relative_path):
                        format_type = "readable"
                    elif "llm" in str(relative_path):
                        format_type = "llm-readable"
                    elif relative_path.parent == Path():
                        format_type = "light"

                    diagram_meta = {
                        "id": file_path.stem,  # filename without extension
                        "name": file_path.stem.replace("_", " ")
                        .replace("-", " ")
                        .title(),
                        "path": str(relative_path),
                        "format": format_type,
                        "extension": file_path.suffix[1:],  # Remove the dot
                        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        "size": stats.st_size,
                    }

                    diagrams.append(diagram_meta)

                except Exception as e:
                    logger.warning(f"Failed to process diagram file {file_path}: {e}")
                    continue

        diagrams.sort(key=lambda x: x["modified"], reverse=True)

        return diagrams

    def load_diagram(self, path: str) -> Dict[str, Any]:
        file_path = self.diagrams_dir / path

        if not file_path.exists():
            logger.error(f"Diagram file not found: {file_path}")
            raise ValidationError(f"Diagram file not found: {path}")

        try:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                with open(file_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            elif file_path.suffix.lower() == ".json":
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
            else:
                raise ValidationError(f"Unsupported file format: {file_path.suffix}")

            if isinstance(data, dict) and "nodes" in data:
                if isinstance(data.get("nodes"), list):
                    data["nodes"] = {n["id"]: n for n in data["nodes"]}
                if isinstance(data.get("arrows"), list):
                    data["arrows"] = {a["id"]: a for a in data["arrows"]}
                if isinstance(data.get("persons"), list):
                    data["persons"] = {p["id"]: p for p in data["persons"]}
                if isinstance(data.get("handles"), list):
                    data["handles"] = {h["id"]: h for h in data["handles"]}
                if "apiKeys" in data and "api_keys" not in data:
                    data["api_keys"] = data.pop("apiKeys")
                if isinstance(data.get("api_keys"), list):
                    data["api_keys"] = {k["id"]: k for k in data["api_keys"]}

                self._validate_and_fix_api_keys(data)

                data.setdefault("nodes", {})
                data.setdefault("arrows", {})
                data.setdefault("handles", {})
                data.setdefault("persons", {})
                data.setdefault("api_keys", {})

                return data
            raise ValidationError("Invalid diagram format")

        except yaml.YAMLError as e:
            raise ValidationError(f"Failed to parse YAML file: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Failed to parse JSON file: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to load diagram: {e}")

    def save_diagram(self, path: str, diagram: Dict[str, Any]) -> None:
        file_path = self.diagrams_dir / path

        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._validate_diagram(diagram)

            if file_path.suffix.lower() in [".yaml", ".yml"]:
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        diagram,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        allow_unicode=True,
                    )
            elif file_path.suffix.lower() == ".json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(diagram, f, indent=2, ensure_ascii=False)
            else:
                raise ValidationError(f"Unsupported file format: {file_path.suffix}")

            logger.info(f"Saved diagram to {path}")

        except Exception as e:
            raise ValidationError(f"Failed to save diagram: {e}")

    def create_diagram(
        self, name: str, diagram: Dict[str, Any], format: str = "json"
    ) -> str:
        safe_name = name.replace(" ", "_").replace("/", "_")
        extension = ".yaml" if format == "yaml" else ".json"
        path = f"{safe_name}{extension}"

        file_path = self.diagrams_dir / path
        if file_path.exists():
            import uuid

            unique_id = str(uuid.uuid4())[:8]
            path = f"{safe_name}_{unique_id}{extension}"

        self.save_diagram(path, diagram)

        return path

    def update_diagram(self, path: str, diagram: Dict[str, Any]) -> None:
        file_path = self.diagrams_dir / path

        if not file_path.exists():
            raise ValidationError(f"Diagram file not found: {path}")

        self.save_diagram(path, diagram)

    def delete_diagram(self, path: str) -> None:
        file_path = self.diagrams_dir / path

        if not file_path.exists():
            raise ValidationError(f"Diagram file not found: {path}")

        try:
            file_path.unlink()
            logger.info(f"Deleted diagram at {path}")
        except Exception as e:
            raise ValidationError(f"Failed to delete diagram: {e}")

    async def save_diagram_with_id(
        self, diagram_dict: Dict[str, Any], filename: str
    ) -> str:
        if filename == "quicksave.json":
            path = "quicksave.json"
            diagram_id = "quicksave"

            if "metadata" not in diagram_dict:
                diagram_dict["metadata"] = {}
            diagram_dict["metadata"]["id"] = diagram_id

            self.save_diagram(path, diagram_dict)
            return diagram_id

        name = diagram_dict.get("metadata", {}).get("name") or Path(filename).stem

        safe_name = name.replace(" ", "_").replace("/", "_")
        extension = ".yaml"

        diagram_id = diagram_dict.get("metadata", {}).get("id")
        if diagram_id:
            path = f"{diagram_id}{extension}"
        else:
            import uuid

            unique_id = str(uuid.uuid4())
            path = f"{safe_name}_{unique_id}{extension}"
            diagram_id = Path(path).stem

            if "metadata" not in diagram_dict:
                diagram_dict["metadata"] = {}
            diagram_dict["metadata"]["id"] = diagram_id

        self.save_diagram(path, diagram_dict)

        return diagram_id

    async def get_diagram(self, diagram_id: DiagramID) -> Optional[Dict[str, Any]]:
        """Get a diagram by ID.

        Args:
            diagram_id: The diagram ID (filename without extension)

        Returns:
            Diagram dictionary or None if not found
        """
        logger.info(f"get_diagram called with diagram_id: {diagram_id}")
        logger.info(f"diagrams_dir: {self.diagrams_dir}")

        if diagram_id == "quicksave":
            json_path = self.diagrams_dir / "quicksave.json"
            logger.info(f"Checking quicksave.json at: {json_path}")
            logger.info(f"File exists: {json_path.exists()}")

            if json_path.exists():
                try:
                    logger.info("Loading quicksave.json...")
                    result = self.load_diagram("quicksave.json")
                    logger.info(
                        f"Successfully loaded quicksave.json, metadata: {result.get('metadata', {})}"
                    )
                    return result
                except Exception as e:
                    logger.error(f"Failed to load quicksave.json: {e}", exc_info=True)

        logger.info(f"Continuing to search for diagram_id: {diagram_id}")

        for ext in [".yaml", ".yml", ".json"]:
            path = f"{diagram_id}{ext}"
            file_path = self.diagrams_dir / path
            if file_path.exists():
                try:
                    return self.load_diagram(path)
                except Exception as e:
                    logger.error(f"Failed to load diagram {path}: {e}")
                    continue

        for file_info in self.list_diagram_files():
            try:
                diagram = self.load_diagram(file_info["path"])
                if diagram.get("metadata", {}).get("id") == diagram_id:
                    return diagram
            except Exception:
                continue

        return None
