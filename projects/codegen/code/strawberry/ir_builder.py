# projects/codegen/code/strawberry/ir_builder.py
from __future__ import annotations
from pathlib import Path
import json
import re
from typing import Any, Dict, List
from datetime import datetime
import yaml

class TypeMapper:
    def __init__(self, cfg):
        self.cfg = cfg

    def ts_to_py(self, ts: str) -> str:
        s = ts.strip()
        # branded scalars
        m = re.search(r"string\s*&\s*{[^']*'__brand':\s*'([^']+)'}", s)
        if m:
            return f"{m.group(1)}"  # NodeID, DiagramID, etc. (handled as scalars)
        # scalar map
        scalars = self.cfg.type_mappings.get("scalar_mappings", {})
        if s in scalars: return scalars[s]
        # collections / records
        if "Record<" in s or "Dict" in s: return "JSONScalar"
        if s.startswith("Array<"): return f"list[{self.ts_to_py(s[6:-1])}]"
        # fall back
        return s

class StrawberryConfig:
    def __init__(self, root: Path):
        self.root = root
        self.type_mappings = self._load("type_mappings.yaml")
        self.domain_fields = self._load("domain_fields.yaml")
        self.schema = self._opt("schema_config.yaml")

    def _load(self, name: str) -> Dict[str, Any]:
        with open(self.root / name, "r") as f:
            return yaml.safe_load(f) or {}

    def _opt(self, name: str) -> Dict[str, Any]:
        p = self.root / name
        return self._load(name) if p.exists() else {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "type_mappings": self.type_mappings,
            "domain_fields": self.domain_fields,
            "schema": self.schema
        }


class IRBuilder:
    def __init__(self, config):
        self.config = config
        self.mapper = TypeMapper(config)

    def build_domain_ir(self, ast_data: Dict) -> Dict:
        """Extract interfaces, scalars, enums, and node specifications from TypeScript AST"""
        domain_ir = {
            "interfaces": [],
            "scalars": [],
            "enums": [],
            "inputs": [],
            "node_specs": []
        }

        # Extract interfaces
        for interface in ast_data.get("interfaces", []):
            interface_name = interface["name"]

            # Check if this interface has special configuration
            interface_config = self.config.domain_fields.get("interfaces", {}).get(interface_name, {})

            interface_def = {
                "name": interface_name,
                "fields": [],
                "field_methods": interface_config.get("field_methods", []),
                "simple_fields": interface_config.get("simple_fields", True),
                "custom_fields": interface_config.get("custom_fields", [])
            }

            # Process fields from AST
            for prop in interface.get("properties", []):
                field = {
                    "name": prop["name"],
                    "type": self.mapper.ts_to_py(prop.get("type", "any")),
                    "is_optional": prop.get("isOptional", False),
                    "description": prop.get("description", "")
                }
                interface_def["fields"].append(field)

            domain_ir["interfaces"].append(interface_def)

        # Extract enums
        # Frontend-only enums that should be skipped for Python/GraphQL generation
        frontend_only_enums = {
            'QueryOperationType', 'CrudOperation', 'QueryEntity',
            'FieldPreset', 'FieldGroup'
        }

        for enum in ast_data.get("enums", []):
            enum_name = enum["name"]

            # Skip frontend-only enums
            if enum_name in frontend_only_enums:
                continue

            # Handle both 'values' and 'members' field names
            enum_values = []

            if "members" in enum:
                # For enums with members (name/value pairs)
                for member in enum.get("members", []):
                    # Create a dict with both name and value
                    enum_values.append({
                        "name": member["name"],
                        "value": member.get("value", member["name"].lower())
                    })
            elif "values" in enum:
                # For simple enum values (just strings)
                for value in enum.get("values", []):
                    if isinstance(value, str):
                        enum_values.append({
                            "name": value,
                            "value": value.lower()
                        })
                    elif isinstance(value, dict):
                        enum_values.append(value)

            enum_def = {
                "name": enum_name,
                "values": enum_values
            }
            domain_ir["enums"].append(enum_def)

        # Extract branded scalars
        for scalar in ast_data.get("brandedScalars", []):
            scalar_def = {
                "name": scalar["brand"],
                "base_type": "strawberry.ID" if "ID" in scalar["brand"] else "str"
            }
            domain_ir["scalars"].append(scalar_def)

        # Also extract scalars from types array (for graphql-inputs.ts format)
        for type_def in ast_data.get("types", []):
            if not isinstance(type_def, dict):
                continue

            name = type_def.get("name", "")

            # Check if it's the Scalars type definition
            if name == "Scalars" and isinstance(type_def.get("type"), str):
                # Parse scalar definitions from the type string
                type_str = type_def["type"]
                # Match patterns like "ApiKeyID: { input: ApiKeyID; output: ApiKeyID; }"
                # Updated pattern to match any word ending with ID (not just starting with word chars)
                scalar_pattern = r'(\w+ID):\s*\{[^}]+\}'
                for match in re.finditer(scalar_pattern, type_str):
                    scalar_name = match.group(1)
                    # Skip base ID but include TaskID and HookID
                    if scalar_name != "ID":
                        scalar_def = {
                            "name": scalar_name,
                            "base_type": "strawberry.ID"
                        }
                        # Avoid duplicates
                        if not any(s["name"] == scalar_name for s in domain_ir["scalars"]):
                            domain_ir["scalars"].append(scalar_def)

            # Check if it's an input type (ends with "Input")
            elif name.endswith("Input") and isinstance(type_def.get("type"), str):
                # Parse the TypeScript type definition to extract fields
                type_str = type_def["type"]
                input_def = {
                    "name": name,
                    "fields": []
                }

                # Parse fields from the type string
                # Match patterns like "field_name: Type" or "field_name?: Type"
                field_pattern = r'(\w+)(\?)?:\s*([^;]+);'
                for match in re.finditer(field_pattern, type_str):
                    field_name = match.group(1)
                    is_optional = match.group(2) == '?'
                    field_type = match.group(3).strip()

                    field_def = {
                        "name": field_name,
                        "type": field_type,  # Keep raw TypeScript type
                        "is_required": not is_optional,
                        "is_optional": is_optional,
                        "description": ""
                    }
                    input_def["fields"].append(field_def)

                if input_def["fields"]:  # Only add if we found fields
                    domain_ir["inputs"].append(input_def)

        # Extract input types from inputs array (original format)
        for input_type in ast_data.get("inputs", []):
            # Skip if not a dict (could be malformed data)
            if not isinstance(input_type, dict):
                continue

            input_def = {
                "name": input_type.get("name", "UnknownInput"),
                "fields": []
            }

            for field in input_type.get("fields", []):
                if not isinstance(field, dict):
                    continue

                field_def = {
                    "name": field.get("name", "unknown"),
                    "type": self.mapper.ts_to_py(field.get("type", "any")),
                    "is_required": field.get("isRequired", False),
                    "description": field.get("description", "")
                }
                input_def["fields"].append(field_def)

            domain_ir["inputs"].append(input_def)

        # Extract node specifications from constants
        for constant in ast_data.get("constants", []):
            if not isinstance(constant, dict):
                continue

            # Check if it's a NodeSpecification constant
            if constant.get("type") == "NodeSpecification" and "value" in constant:
                spec = constant["value"]
                if not isinstance(spec, dict):
                    continue

                # Extract node type and convert to class name
                node_type = spec.get("nodeType", "")
                # Convert "NodeType.API_JOB" to "ApiJob"
                if node_type.startswith("NodeType."):
                    type_name = node_type.replace("NodeType.", "")
                    # Convert SNAKE_CASE to PascalCase
                    parts = type_name.split("_")
                    class_name = "".join(part.capitalize() for part in parts)
                else:
                    class_name = node_type

                # Build node spec definition
                node_spec_def = {
                    "class_name": class_name,
                    "display_name": spec.get("displayName", class_name),
                    "pydantic_model": class_name,
                    "description": spec.get("description", ""),
                    "category": spec.get("category", ""),
                    "icon": spec.get("icon", ""),
                    "color": spec.get("color", ""),
                    "fields": []
                }

                # Process node fields
                for field in spec.get("fields", []):
                    if not isinstance(field, dict):
                        continue

                    # Determine if field is dict type
                    field_type = field.get("type", "string")
                    is_dict_type = field_type in ["object", "dict", "Record", "Dict"]

                    field_def = {
                        "name": field.get("name", ""),
                        "type": self.mapper.ts_to_py(field_type),
                        "required": field.get("required", False),
                        "is_dict_type": is_dict_type,
                        "description": field.get("description", "")
                    }
                    node_spec_def["fields"].append(field_def)

                domain_ir["node_specs"].append(node_spec_def)

        return domain_ir

    def build_operations_ir(self, ops_meta: List[Dict]) -> Dict:
        """Build operations IR from metadata"""
        operations_ir = {
            "queries": [],
            "mutations": [],
            "subscriptions": []
        }

        for op in ops_meta:
            operation_def = {
                "name": op["name"],
                "returns": op["returns"],
                "variables": op.get("variables", []),
                "description": op.get("description", "")
            }

            # Categorize by operation type
            if op["kind"] == "query":
                operations_ir["queries"].append(operation_def)
            elif op["kind"] == "mutation":
                operations_ir["mutations"].append(operation_def)
            elif op["kind"] == "subscription":
                operations_ir["subscriptions"].append(operation_def)

        return operations_ir

    def merge_to_strawberry_ir(self, domain_ir: Dict, ops_ir: Dict) -> Dict:
        """Merge all IRs into final strawberry_ir.json"""
        return {
            "version": 1,
            "generated_at": datetime.now().isoformat(),
            "interfaces": domain_ir["interfaces"],
            "scalars": domain_ir["scalars"],
            "enums": domain_ir["enums"],
            "inputs": domain_ir["inputs"],
            "node_specs": domain_ir.get("node_specs", []),
            "operations": ops_ir,
            "result_wrappers": self._generate_result_wrappers(ops_ir),
            "metadata": {}  # Initialize metadata dict
        }

    def _generate_result_wrappers(self, ops_ir: Dict) -> List[Dict]:
        """Generate result wrapper types for mutations"""
        wrappers = set()

        for mutation in ops_ir.get("mutations", []):
            return_type = mutation.get("returns", "")
            if "Result" in return_type:
                wrappers.add(return_type)

        result_wrappers = []
        for wrapper_name in sorted(wrappers):
            # Determine the base type from the wrapper name
            if wrapper_name == "ExecutionResult":
                base_type = "ExecutionStateType"
            elif wrapper_name == "DiagramResult":
                base_type = "DomainDiagramType"
            elif wrapper_name == "NodeResult":
                base_type = "DomainNodeType"
            elif wrapper_name == "PersonResult":
                base_type = "DomainPersonType"
            elif wrapper_name == "ApiKeyResult":
                base_type = "DomainApiKeyType"
            elif wrapper_name == "DeleteResult":
                base_type = None  # Delete results don't have a data field
            elif wrapper_name == "CliSessionResult":
                base_type = "CliSessionType"
            elif wrapper_name == "FileOperationResult":
                base_type = "FileTypeType"
            elif wrapper_name == "FormatConversionResult":
                base_type = "str"  # or appropriate type for format conversion
            else:
                base_type = "JSON"

            wrapper_def = {
                "name": wrapper_name,
                "base_type": base_type,
                "fields": [
                    {"name": "success", "type": "bool"},
                    {"name": "message", "type": "Optional[str]"}
                ]
            }

            if base_type:
                wrapper_def["fields"].append({
                    "name": "data",
                    "type": f"Optional[{base_type}]"
                })

            result_wrappers.append(wrapper_def)

        return result_wrappers

    def build_and_save(self, ast_data: Dict, ops_meta_path: Path = None, output_path: Path = None) -> Dict:
        """Build complete IR and save to file"""
        # Load operations metadata if available
        ops_meta = []
        if ops_meta_path and ops_meta_path.exists():
            ops_meta = json.loads(ops_meta_path.read_text())

        # Build IRs
        domain_ir = self.build_domain_ir(ast_data)
        ops_ir = self.build_operations_ir(ops_meta)

        # Merge to final IR
        strawberry_ir = self.merge_to_strawberry_ir(domain_ir, ops_ir)

        # Save if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(strawberry_ir, indent=2))

        return strawberry_ir


def build_complete_ir(input_data) -> Dict[str, Any]:
    """
    Build complete Strawberry IR from TypeScript AST files and configuration.
    This is the main entry point called by the diagram.

    Args:
        input_data: Input from the db node - can be a dict or list of dicts

    Returns:
        Complete strawberry IR for template rendering
    """
    # 1. Load configuration (use absolute path)
    import os
    base_dir = Path(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))
    config_path = base_dir / "projects/codegen/config/strawberry"
    config = StrawberryConfig(config_path)

    # Create IR builder instance
    builder = IRBuilder(config)

    # 2. Handle input data - the db node always wraps in 'default' key
    ast_files = []

    # Extract the file path dictionary from the 'default' key
    file_dict = input_data.get("default", {})

    # Files to exclude from domain type generation
    exclude_patterns = [
        'ast-types.ts',  # AST parsing types
        'query-specifications.ts',  # Frontend query types
        'relationship-queries.ts',  # Frontend relationship configs
    ]

    # Each key is a file path, each value is the AST content
    for file_path, ast_content in file_dict.items():
        # Skip files that should be excluded from domain types
        if any(pattern in file_path for pattern in exclude_patterns):
            print(f"Skipping excluded file: {file_path}")
            continue

        if isinstance(ast_content, dict):
            ast_files.append(ast_content)
        elif isinstance(ast_content, list):
            ast_files.extend(ast_content)

    # 3. Merge all AST files into a single structure
    merged_ast = {
        "interfaces": [],
        "enums": [],
        "brandedScalars": [],
        "inputs": [],
        "types": [],  # Add types array
        "constants": []  # Add constants array for node specs
    }

    for ast_file in ast_files:
        if not isinstance(ast_file, dict):
            continue
        # Each file can have multiple interfaces, enums, etc.
        if "interfaces" in ast_file:
            merged_ast["interfaces"].extend(ast_file["interfaces"])
        if "enums" in ast_file:
            merged_ast["enums"].extend(ast_file["enums"])
        if "brandedScalars" in ast_file:
            merged_ast["brandedScalars"].extend(ast_file["brandedScalars"])
        if "inputs" in ast_file:
            merged_ast["inputs"].extend(ast_file["inputs"])
        if "types" in ast_file:
            merged_ast["types"].extend(ast_file["types"])
        if "constants" in ast_file:
            merged_ast["constants"].extend(ast_file["constants"])

    # 4. Build domain IR from merged AST
    print(f"Processing {len(ast_files)} AST files")
    print(f"Merged AST has {len(merged_ast['enums'])} enums")
    print(f"Merged AST has {len(merged_ast['constants'])} constants")
    print(f"Enum names: {[e['name'] for e in merged_ast['enums']]}")

    domain_ir = builder.build_domain_ir(merged_ast)
    print(f"Domain IR has {len(domain_ir['enums'])} enums after build")
    print(f"Domain IR has {len(domain_ir.get('node_specs', []))} node specs after build")
    print(f"Domain IR enum names: {[e['name'] for e in domain_ir['enums']]}")
    print(f"Node spec names: {[n['class_name'] for n in domain_ir.get('node_specs', [])]}")

    # 5. Generate operations metadata
    # Note: We need to generate operations metadata from the query definitions
    # For now, we'll try to load existing metadata if available
    ops_meta_path = base_dir / "dipeo/diagram_generated_staged/graphql/operations_meta.json"
    if not ops_meta_path.exists():
        ops_meta_path = base_dir / "dipeo/diagram_generated/graphql/operations_meta.json"

    ops_meta = []
    if ops_meta_path.exists():
        ops_meta = json.loads(ops_meta_path.read_text())
        print(f"Loaded {len(ops_meta)} operations from metadata")

    # 6. Build operations IR
    ops_ir = builder.build_operations_ir(ops_meta)

    # 7. Merge to final strawberry IR
    strawberry_ir = builder.merge_to_strawberry_ir(domain_ir, ops_ir)

    # 8. Add additional metadata for templates
    strawberry_ir["config"] = config.to_dict()
    strawberry_ir["metadata"]["ast_file_count"] = len(ast_files)
    strawberry_ir["metadata"]["interface_count"] = len(domain_ir["interfaces"])
    strawberry_ir["metadata"]["enum_count"] = len(domain_ir["enums"])
    strawberry_ir["metadata"]["scalar_count"] = len(domain_ir["scalars"])
    strawberry_ir["metadata"]["input_count"] = len(domain_ir["inputs"])

    # 9. Process types for Strawberry-specific formatting
    strawberry_ir["types"] = _process_types_for_strawberry(strawberry_ir["interfaces"])

    # 10. Write IR to file for debugging/inspection
    ir_output_path = base_dir / "projects/codegen/ir/strawberry_ir.json"
    ir_output_path.parent.mkdir(parents=True, exist_ok=True)
    ir_output_path.write_text(json.dumps(strawberry_ir, indent=2))
    print(f"Wrote strawberry IR to {ir_output_path}")

    return strawberry_ir


def _process_types_for_strawberry(interfaces: List[Dict]) -> List[Dict]:
    """
    Process interfaces to create Strawberry type definitions.
    """
    types = []

    for interface in interfaces:
        strawberry_type = {
            "name": interface["name"],
            "fields": [],
            "field_methods": interface.get("field_methods", []),
            "custom_fields": interface.get("custom_fields", [])
        }

        # Process regular fields
        for field in interface["fields"]:
            strawberry_field = {
                "name": field["name"],
                "type": _convert_to_strawberry_type(field["type"]),
                "is_optional": field.get("is_optional", False),
                "description": field.get("description", "")
            }
            strawberry_type["fields"].append(strawberry_field)

        types.append(strawberry_type)

    return types


def _convert_to_strawberry_type(py_type: str) -> str:
    """
    Convert Python type to Strawberry GraphQL type.
    """
    # Map Python types to Strawberry types
    type_map = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "dict": "JSON",
        "Dict": "JSON",
        "Dict[str, Any]": "JSON",
        "list": "List",
        "List": "List",
        "Optional": "Optional",
        "Any": "JSON",
        "datetime": "DateTime",
    }

    # Handle Optional types
    if py_type.startswith("Optional["):
        inner_type = py_type[9:-1]
        return f"Optional[{_convert_to_strawberry_type(inner_type)}]"

    # Handle List types
    if py_type.startswith("List[") or py_type.startswith("list["):
        inner_type = py_type[5:-1]
        return f"List[{_convert_to_strawberry_type(inner_type)}]"

    # Direct mapping or return as-is
    return type_map.get(py_type, py_type)
