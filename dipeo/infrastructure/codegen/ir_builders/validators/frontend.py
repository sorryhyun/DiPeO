"""Frontend IR data validator."""

from __future__ import annotations

from typing import Any

from .base import BaseValidator, ValidationResult


class FrontendValidator(BaseValidator):
    """Validator for frontend IR data."""

    def __init__(self):
        """Initialize frontend validator."""
        super().__init__("FrontendValidator")

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate frontend IR data.

        Args:
            data: Frontend IR data to validate

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check required top-level fields
        required_fields = [
            "version",
            "generated_at",
            "node_specs",
            "node_configs",
            "node_registry",
            "field_configs",
            "typescript_models",
            "graphql_queries",
        ]
        result.merge(self.check_required_fields(data, required_fields))

        # Check field types
        field_types = {
            "version": (int, float),
            "generated_at": str,
            "node_specs": list,
            "node_configs": dict,
            "node_registry": dict,
            "field_configs": dict,
            "typescript_models": dict,
            "graphql_queries": list,
            "grouped_queries": dict,
            "enums": list,
            "metadata": dict,
        }
        result.merge(self.check_field_types(data, field_types))

        # Validate node configs
        if "node_configs" in data and isinstance(data["node_configs"], dict):
            result.merge(self._validate_node_configs(data["node_configs"]))

        # Validate field configs
        if "field_configs" in data and isinstance(data["field_configs"], dict):
            result.merge(self._validate_field_configs(data["field_configs"]))

        # Validate GraphQL queries
        if "graphql_queries" in data and isinstance(data["graphql_queries"], list):
            result.merge(self._validate_graphql_queries(data["graphql_queries"]))

        # Check consistency
        consistency_checks = [
            ("node_config_coverage", self._check_node_config_coverage),
            ("field_config_validity", self._check_field_config_validity),
            ("query_grouping", self._check_query_grouping),
            ("metadata_consistency", self._check_metadata_consistency),
        ]
        result.merge(self.check_consistency(data, consistency_checks))

        return result

    def _validate_node_configs(self, node_configs: dict) -> ValidationResult:
        """Validate node configurations.

        Args:
            node_configs: Node configuration dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not node_configs:
            result.add_warning("node_configs", "No node configurations found")
            return result

        for node_name, config in node_configs.items():
            if not isinstance(config, dict):
                result.add_error(f"node_configs.{node_name}", "Node config must be a dictionary")
                continue

            # Check for required UI config fields
            ui_fields = ["label", "category", "icon", "color"]
            for field in ui_fields:
                if field not in config:
                    result.add_warning(
                        f"node_configs.{node_name}.{field}",
                        f"Missing UI field '{field}' in node config",
                    )

            # Check for input/output configs
            if "inputs" in config:
                if not isinstance(config["inputs"], list | dict):
                    result.add_error(
                        f"node_configs.{node_name}.inputs", "Inputs must be a list or dictionary"
                    )

            if "outputs" in config:
                if not isinstance(config["outputs"], list | dict):
                    result.add_error(
                        f"node_configs.{node_name}.outputs", "Outputs must be a list or dictionary"
                    )

        return result

    def _validate_field_configs(self, field_configs: dict) -> ValidationResult:
        """Validate field configurations.

        Args:
            field_configs: Field configuration dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not field_configs:
            result.add_warning("field_configs", "No field configurations found")
            return result

        for field_name, config in field_configs.items():
            if not isinstance(config, dict):
                result.add_error(f"field_configs.{field_name}", "Field config must be a dictionary")
                continue

            # Check for common field config properties
            if "type" not in config:
                result.add_warning(
                    f"field_configs.{field_name}.type", "Missing 'type' in field config"
                )

            if "component" in config:
                # Validate component configuration
                component = config["component"]
                if not isinstance(component, str | dict):
                    result.add_error(
                        f"field_configs.{field_name}.component",
                        "Component must be a string or dictionary",
                    )

        return result

    def _validate_graphql_queries(self, queries: list) -> ValidationResult:
        """Validate GraphQL queries.

        Args:
            queries: List of GraphQL queries

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not queries:
            result.add_warning("graphql_queries", "No GraphQL queries found")
            return result

        for i, query in enumerate(queries):
            if not isinstance(query, dict):
                result.add_error(f"graphql_queries[{i}]", "Query must be a dictionary")
                continue

            # Check required query fields
            required = ["name", "type"]
            for field in required:
                if field not in query:
                    result.add_error(
                        f"graphql_queries[{i}].{field}",
                        f"Missing required field '{field}' in query",
                    )

            # Validate query type
            if "type" in query:
                valid_types = ["query", "mutation", "subscription"]
                if query["type"] not in valid_types:
                    result.add_error(
                        f"graphql_queries[{i}].type",
                        f"Invalid query type: {query['type']}. Must be one of {valid_types}",
                    )

            # Check for query string or fields
            if "query" not in query and "fields" not in query:
                result.add_warning(
                    f"graphql_queries[{i}]",
                    "Query has neither 'query' string nor 'fields' definition",
                )

        return result

    def _check_node_config_coverage(self, data: dict) -> tuple[bool, str]:
        """Check if all node specs have configs.

        Args:
            data: Frontend IR data

        Returns:
            (success, message) tuple
        """
        if "node_specs" not in data or "node_configs" not in data:
            return True, "Skipping coverage check - missing data"

        node_specs = data["node_specs"]
        node_configs = data["node_configs"]

        # Collect node names from specs
        spec_names = {
            spec["name"] for spec in node_specs if isinstance(spec, dict) and "name" in spec
        }

        # Collect node names from configs
        config_names = set(node_configs.keys())

        # Check coverage
        missing = spec_names - config_names
        if missing:
            # This is a warning, not an error
            return True, f"Nodes without configs (warning): {', '.join(sorted(missing))}"

        extra = config_names - spec_names
        if extra:
            return False, f"Configs for non-existent nodes: {', '.join(sorted(extra))}"

        return True, "Node config coverage check passed"

    def _check_field_config_validity(self, data: dict) -> tuple[bool, str]:
        """Check field config validity.

        Args:
            data: Frontend IR data

        Returns:
            (success, message) tuple
        """
        if "field_configs" not in data:
            return True, "No field configs to validate"

        field_configs = data["field_configs"]

        # Check for common issues
        invalid_types = []
        for field_name, config in field_configs.items():
            if isinstance(config, dict) and "type" in config:
                field_type = config["type"]
                # Check for common valid types
                valid_types = ["string", "number", "boolean", "array", "object", "any"]
                if not any(vt in str(field_type).lower() for vt in valid_types):
                    invalid_types.append(f"{field_name}:{field_type}")

        if invalid_types:
            return False, f"Potentially invalid field types: {', '.join(invalid_types[:5])}"

        return True, "Field config validity check passed"

    def _check_query_grouping(self, data: dict) -> tuple[bool, str]:
        """Check GraphQL query grouping consistency.

        Args:
            data: Frontend IR data

        Returns:
            (success, message) tuple
        """
        if "graphql_queries" not in data or "grouped_queries" not in data:
            return True, "Skipping query grouping check - missing data"

        queries = data["graphql_queries"]
        grouped = data["grouped_queries"]

        # Count queries in groups
        grouped_count = sum(
            len(entity_queries) if isinstance(entity_queries, list) else 1
            for entity_queries in grouped.values()
        )

        # Compare counts (grouped might have fewer if some queries aren't grouped)
        if grouped_count > len(queries):
            return (
                False,
                f"More queries in groups ({grouped_count}) than total queries ({len(queries)})",
            )

        return True, "Query grouping check passed"

    def _check_metadata_consistency(self, data: dict) -> tuple[bool, str]:
        """Check metadata consistency.

        Args:
            data: Frontend IR data

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

        # Check config count
        if "config_count" in metadata and "node_configs" in data:
            actual_count = len(data["node_configs"])
            reported_count = metadata["config_count"]
            if actual_count != reported_count:
                return (
                    False,
                    f"Config count mismatch: actual={actual_count}, reported={reported_count}",
                )

        # Check query count
        if "query_count" in metadata and "graphql_queries" in data:
            actual_count = len(data["graphql_queries"])
            reported_count = metadata["query_count"]
            if actual_count != reported_count:
                return (
                    False,
                    f"Query count mismatch: actual={actual_count}, reported={reported_count}",
                )

        return True, "Metadata consistency check passed"
