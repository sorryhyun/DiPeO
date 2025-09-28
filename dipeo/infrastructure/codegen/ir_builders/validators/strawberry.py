"""Strawberry (GraphQL) IR data validator."""

from __future__ import annotations

from typing import Any

from .base import BaseValidator, ValidationResult


class StrawberryValidator(BaseValidator):
    """Validator for Strawberry GraphQL IR data."""

    def __init__(self):
        """Initialize Strawberry validator."""
        super().__init__("StrawberryValidator")

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate Strawberry IR data.

        Args:
            data: Strawberry IR data to validate

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check required top-level fields
        required_fields = [
            "version",
            "generated_at",
            "operations",
            "domain",
            "inputs",
            "results",
            "enums",
        ]
        result.merge(self.check_required_fields(data, required_fields))

        # Check field types
        field_types = {
            "version": str,
            "generated_at": str,
            "operations": dict,
            "domain": dict,
            "inputs": dict,
            "results": dict,
            "enums": dict,
            "config": dict,
            "node_specs": list,
        }
        result.merge(self.check_field_types(data, field_types))

        # Validate operations
        if "operations" in data and isinstance(data["operations"], dict):
            result.merge(self._validate_operations(data["operations"]))

        # Validate domain types
        if "domain" in data and isinstance(data["domain"], dict):
            result.merge(self._validate_domain(data["domain"]))

        # Validate input types
        if "inputs" in data and isinstance(data["inputs"], dict):
            result.merge(self._validate_inputs(data["inputs"]))

        # Validate result types
        if "results" in data and isinstance(data["results"], dict):
            result.merge(self._validate_results(data["results"]))

        # Check consistency
        consistency_checks = [
            ("operation_type_references", self._check_operation_type_references),
            ("enum_consistency", self._check_enum_consistency),
            ("domain_field_coverage", self._check_domain_field_coverage),
        ]
        result.merge(self.check_consistency(data, consistency_checks))

        return result

    def _validate_operations(self, operations: dict) -> ValidationResult:
        """Validate GraphQL operations.

        Args:
            operations: Operations dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check for required operation fields
        required_fields = ["operations", "queries", "mutations"]
        for field in required_fields:
            if field not in operations:
                result.add_error(f"operations.{field}", f"Missing required field '{field}'")

        # Validate individual operations
        if "operations" in operations and isinstance(operations["operations"], list):
            for i, op in enumerate(operations["operations"]):
                if not isinstance(op, dict):
                    result.add_error(
                        f"operations.operations[{i}]", "Operation must be a dictionary"
                    )
                    continue

                # Check operation structure
                if "name" not in op:
                    result.add_error(f"operations.operations[{i}].name", "Operation missing 'name'")
                if "type" not in op:
                    result.add_error(f"operations.operations[{i}].type", "Operation missing 'type'")
                elif op["type"] not in ["query", "mutation", "subscription"]:
                    result.add_error(
                        f"operations.operations[{i}].type", f"Invalid operation type: {op['type']}"
                    )

                # Check for variables or fields
                if "variables" not in op and "fields" not in op:
                    result.add_warning(
                        f"operations.operations[{i}]", "Operation has neither variables nor fields"
                    )

        # Validate query strings
        if "queries" in operations and isinstance(operations["queries"], dict):
            for query_name, query_string in operations["queries"].items():
                if not isinstance(query_string, str):
                    result.add_error(
                        f"operations.queries.{query_name}", "Query string must be a string"
                    )
                elif not query_string.strip():
                    result.add_error(f"operations.queries.{query_name}", "Query string is empty")

        # Validate mutation strings
        if "mutations" in operations and isinstance(operations["mutations"], dict):
            for mutation_name, mutation_string in operations["mutations"].items():
                if not isinstance(mutation_string, str):
                    result.add_error(
                        f"operations.mutations.{mutation_name}", "Mutation string must be a string"
                    )
                elif not mutation_string.strip():
                    result.add_error(
                        f"operations.mutations.{mutation_name}", "Mutation string is empty"
                    )

        return result

    def _validate_domain(self, domain: dict) -> ValidationResult:
        """Validate domain types.

        Args:
            domain: Domain dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Check for domain types
        if "types" not in domain:
            result.add_error("domain.types", "Missing 'types' in domain")
        elif not isinstance(domain["types"], list):
            result.add_error("domain.types", "'types' must be a list")
        else:
            for i, domain_type in enumerate(domain["types"]):
                if not isinstance(domain_type, dict):
                    result.add_error(f"domain.types[{i}]", "Domain type must be a dictionary")
                    continue

                # Check required fields
                if "name" not in domain_type:
                    result.add_error(f"domain.types[{i}].name", "Domain type missing 'name'")
                if "fields" not in domain_type:
                    result.add_warning(f"domain.types[{i}].fields", "Domain type missing 'fields'")

        # Check for fields configuration
        if "fields" in domain and not isinstance(domain["fields"], dict):
            result.add_error("domain.fields", "'fields' must be a dictionary")

        return result

    def _validate_inputs(self, inputs: dict) -> ValidationResult:
        """Validate input types.

        Args:
            inputs: Input types dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        for input_name, input_def in inputs.items():
            if not isinstance(input_def, dict):
                result.add_error(f"inputs.{input_name}", "Input type must be a dictionary")
                continue

            # Check for required fields
            if "fields" not in input_def:
                result.add_warning(f"inputs.{input_name}.fields", "Input type missing 'fields'")
            elif isinstance(input_def["fields"], dict):
                # Validate field definitions
                for field_name, field_def in input_def["fields"].items():
                    if not isinstance(field_def, dict):
                        result.add_error(
                            f"inputs.{input_name}.fields.{field_name}",
                            "Field definition must be a dictionary",
                        )
                    elif "type" not in field_def:
                        result.add_warning(
                            f"inputs.{input_name}.fields.{field_name}.type", "Field missing 'type'"
                        )

        return result

    def _validate_results(self, results: dict) -> ValidationResult:
        """Validate result types.

        Args:
            results: Result types dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        for result_name, result_def in results.items():
            if not isinstance(result_def, dict):
                result.add_error(f"results.{result_name}", "Result type must be a dictionary")
                continue

            # Check for required fields
            if "fields" not in result_def:
                result.add_warning(f"results.{result_name}.fields", "Result type missing 'fields'")
            elif isinstance(result_def["fields"], dict):
                # Validate field definitions
                for field_name, field_def in result_def["fields"].items():
                    if not isinstance(field_def, dict):
                        result.add_error(
                            f"results.{result_name}.fields.{field_name}",
                            "Field definition must be a dictionary",
                        )
                    elif "type" not in field_def:
                        result.add_warning(
                            f"results.{result_name}.fields.{field_name}.type",
                            "Field missing 'type'",
                        )

        return result

    def _check_operation_type_references(self, data: dict) -> tuple[bool, str]:
        """Check if operations reference valid types.

        Args:
            data: Strawberry IR data

        Returns:
            (success, message) tuple
        """
        if "operations" not in data or "inputs" not in data or "results" not in data:
            return True, "Skipping type reference check - missing data"

        operations = data["operations"].get("operations", [])
        input_types = set(data["inputs"].keys())
        result_types = set(data["results"].keys())

        invalid_refs = []

        for op in operations:
            if not isinstance(op, dict):
                continue

            # Check input type references
            if "input_type" in op:
                input_type = op["input_type"]
                if input_type and input_type not in input_types:
                    invalid_refs.append(f"{op.get('name', 'unknown')}.input_type:{input_type}")

            # Check result type references
            if "result_type" in op:
                result_type = op["result_type"]
                if result_type and result_type not in result_types:
                    invalid_refs.append(f"{op.get('name', 'unknown')}.result_type:{result_type}")

        if invalid_refs:
            return False, f"Invalid type references: {', '.join(invalid_refs[:5])}"

        return True, "Operation type references valid"

    def _check_enum_consistency(self, data: dict) -> tuple[bool, str]:
        """Check enum consistency across different sections.

        Args:
            data: Strawberry IR data

        Returns:
            (success, message) tuple
        """
        if "enums" not in data:
            return True, "No enums to check"

        enums = data["enums"]

        # Check enum structure
        for enum_name, enum_def in enums.items():
            if not isinstance(enum_def, dict | list):
                return False, f"Enum '{enum_name}' has invalid structure"

            if isinstance(enum_def, dict):
                if "values" not in enum_def:
                    return False, f"Enum '{enum_name}' missing 'values' field"

        return True, "Enum consistency check passed"

    def _check_domain_field_coverage(self, data: dict) -> tuple[bool, str]:
        """Check domain field configuration coverage.

        Args:
            data: Strawberry IR data

        Returns:
            (success, message) tuple
        """
        if "domain" not in data:
            return True, "No domain data to check"

        domain = data["domain"]

        if "types" not in domain or "fields" not in domain:
            return True, "Skipping field coverage - incomplete domain data"

        types = domain["types"]
        field_configs = domain.get("fields", {})

        # Check if configured fields actually exist in types
        configured_types = set(field_configs.keys())
        actual_types = {t["name"] for t in types if isinstance(t, dict) and "name" in t}

        invalid_configs = configured_types - actual_types
        if invalid_configs:
            return (
                False,
                f"Field configs for non-existent types: {', '.join(sorted(invalid_configs))}",
            )

        return True, "Domain field coverage check passed"
