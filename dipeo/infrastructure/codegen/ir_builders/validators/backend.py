"""Backend IR data validator."""

from __future__ import annotations

from typing import Any

from .base import BaseValidator, ValidationResult


class BackendValidator(BaseValidator):
    """Validator for backend IR data."""

    def __init__(self):
        """Initialize backend validator."""
        super().__init__("BackendValidator")

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate backend IR data.

        Args:
            data: Backend IR data to validate

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check required top-level fields
        required_fields = [
            "version",
            "generated_at",
            "node_specs",
            "enums",
            "domain_models",
            "types",
            "type_aliases",
            "node_factory",
            "integrations",
            "conversions",
        ]
        result.merge(self.check_required_fields(data, required_fields))

        # Check field types
        field_types = {
            "version": (int, float),
            "generated_at": str,
            "node_specs": list,
            "enums": list,
            "domain_models": dict,
            "types": list,
            "type_aliases": dict,
            "node_factory": dict,
            "integrations": list,
            "conversions": dict,
            "typescript_indexes": dict,
            "metadata": dict,
        }
        result.merge(self.check_field_types(data, field_types))

        # Validate node specs
        if "node_specs" in data and isinstance(data["node_specs"], list):
            result.merge(self._validate_node_specs(data["node_specs"]))

        # Validate domain models
        if "domain_models" in data and isinstance(data["domain_models"], dict):
            result.merge(self._validate_domain_models(data["domain_models"]))

        # Validate node factory
        if "node_factory" in data and isinstance(data["node_factory"], dict):
            result.merge(self._validate_node_factory(data["node_factory"]))

        # Check consistency
        consistency_checks = [
            ("node_factory_coverage", self._check_node_factory_coverage),
            ("type_consistency", self._check_type_consistency),
            ("metadata_consistency", self._check_metadata_consistency),
        ]
        result.merge(self.check_consistency(data, consistency_checks))

        return result

    def _validate_node_specs(self, node_specs: list) -> ValidationResult:
        """Validate node specifications.

        Args:
            node_specs: List of node specs

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not node_specs:
            result.add_warning("node_specs", "No node specifications found")
            return result

        for i, spec in enumerate(node_specs):
            if not isinstance(spec, dict):
                result.add_error(f"node_specs[{i}]", "Node spec must be a dictionary")
                continue

            # Check required node spec fields
            required = ["name", "category", "inputs", "outputs"]
            for field in required:
                if field not in spec:
                    result.add_error(
                        f"node_specs[{i}].{field}", f"Missing required field '{field}' in node spec"
                    )

            # Validate inputs and outputs
            if "inputs" in spec and isinstance(spec["inputs"], list):
                for j, input_spec in enumerate(spec["inputs"]):
                    if not isinstance(input_spec, dict):
                        result.add_error(
                            f"node_specs[{i}].inputs[{j}]", "Input spec must be a dictionary"
                        )
                    elif "name" not in input_spec or "type" not in input_spec:
                        result.add_error(
                            f"node_specs[{i}].inputs[{j}]",
                            "Input spec must have 'name' and 'type' fields",
                        )

            if "outputs" in spec and isinstance(spec["outputs"], list):
                for j, output_spec in enumerate(spec["outputs"]):
                    if not isinstance(output_spec, dict):
                        result.add_error(
                            f"node_specs[{i}].outputs[{j}]", "Output spec must be a dictionary"
                        )
                    elif "name" not in output_spec or "type" not in output_spec:
                        result.add_error(
                            f"node_specs[{i}].outputs[{j}]",
                            "Output spec must have 'name' and 'type' fields",
                        )

        return result

    def _validate_domain_models(self, domain_models: dict) -> ValidationResult:
        """Validate domain models.

        Args:
            domain_models: Domain models dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check required structure
        if "models" not in domain_models:
            result.add_error("domain_models.models", "Missing 'models' in domain_models")
        elif not isinstance(domain_models["models"], list):
            result.add_error("domain_models.models", "'models' must be a list")

        if "aliases" not in domain_models:
            result.add_error("domain_models.aliases", "Missing 'aliases' in domain_models")
        elif not isinstance(domain_models["aliases"], dict):
            result.add_error("domain_models.aliases", "'aliases' must be a dictionary")

        # Validate individual models
        if "models" in domain_models and isinstance(domain_models["models"], list):
            for i, model in enumerate(domain_models["models"]):
                if not isinstance(model, dict):
                    result.add_error(f"domain_models.models[{i}]", "Model must be a dictionary")
                elif "name" not in model:
                    result.add_error(f"domain_models.models[{i}]", "Model missing 'name' field")
                elif "fields" not in model:
                    result.add_warning(f"domain_models.models[{i}]", "Model missing 'fields'")

        return result

    def _validate_node_factory(self, node_factory: dict) -> ValidationResult:
        """Validate node factory data.

        Args:
            node_factory: Node factory dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check for categories
        if not node_factory:
            result.add_warning("node_factory", "Node factory is empty")
            return result

        for category, nodes in node_factory.items():
            if not isinstance(nodes, list):
                result.add_error(
                    f"node_factory.{category}", "Category must contain a list of nodes"
                )
                continue

            for i, node in enumerate(nodes):
                if not isinstance(node, dict):
                    result.add_error(
                        f"node_factory.{category}[{i}]", "Node entry must be a dictionary"
                    )
                elif "name" not in node:
                    result.add_error(
                        f"node_factory.{category}[{i}]", "Node entry missing 'name' field"
                    )

        return result

    def _check_node_factory_coverage(self, data: dict) -> tuple[bool, str]:
        """Check if all node specs are in the factory.

        Args:
            data: Backend IR data

        Returns:
            (success, message) tuple
        """
        if "node_specs" not in data or "node_factory" not in data:
            return True, "Skipping coverage check - missing data"

        node_specs = data["node_specs"]
        node_factory = data["node_factory"]

        # Collect all node names from specs
        spec_names = {
            spec["name"] for spec in node_specs if isinstance(spec, dict) and "name" in spec
        }

        # Collect all node names from factory
        factory_names = set()
        for category_nodes in node_factory.values():
            if isinstance(category_nodes, list):
                for node in category_nodes:
                    if isinstance(node, dict) and "name" in node:
                        factory_names.add(node["name"])

        # Check coverage
        missing = spec_names - factory_names
        if missing:
            return False, f"Nodes in specs but not in factory: {', '.join(sorted(missing))}"

        extra = factory_names - spec_names
        if extra:
            return False, f"Nodes in factory but not in specs: {', '.join(sorted(extra))}"

        return True, "All nodes covered"

    def _check_type_consistency(self, data: dict) -> tuple[bool, str]:
        """Check type consistency between types and type_aliases.

        Args:
            data: Backend IR data

        Returns:
            (success, message) tuple
        """
        if "types" not in data or "type_aliases" not in data:
            return True, "Skipping type consistency - missing data"

        types = data["types"]
        type_aliases = data["type_aliases"]

        # Check that types list matches domain_models.models
        if "domain_models" in data and isinstance(data["domain_models"], dict):
            domain_types = data["domain_models"].get("models", [])
            if len(types) != len(domain_types):
                return (
                    False,
                    f"Type count mismatch: types={len(types)}, domain_models.models={len(domain_types)}",
                )

        return True, "Type consistency check passed"

    def _check_metadata_consistency(self, data: dict) -> tuple[bool, str]:
        """Check metadata consistency.

        Args:
            data: Backend IR data

        Returns:
            (success, message) tuple
        """
        if "metadata" not in data:
            return True, "No metadata to check"

        metadata = data["metadata"]

        # Check node count
        if "node_count" in metadata and "node_specs" in data:
            actual_count = len(data["node_specs"])
            reported_count = metadata["node_count"]
            if actual_count != reported_count:
                return (
                    False,
                    f"Node count mismatch: actual={actual_count}, reported={reported_count}",
                )

        # Check enum count
        if "enum_count" in metadata and "enums" in data:
            actual_count = len(data["enums"])
            reported_count = metadata["enum_count"]
            if actual_count != reported_count:
                return (
                    False,
                    f"Enum count mismatch: actual={actual_count}, reported={reported_count}",
                )

        # Check model count
        if "model_count" in metadata and "types" in data:
            actual_count = len(data["types"])
            reported_count = metadata["model_count"]
            if actual_count != reported_count:
                return (
                    False,
                    f"Model count mismatch: actual={actual_count}, reported={reported_count}",
                )

        return True, "Metadata consistency check passed"
