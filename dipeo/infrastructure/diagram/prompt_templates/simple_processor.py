"""Simple template processor implementing the domain port."""

import json
import re
from datetime import datetime
from typing import Any

from dipeo.domain.diagram.ports import TemplateProcessorPort, TemplateResult


class SimpleTemplateProcessor(TemplateProcessorPort):
    """Simple template processor supporting legacy double-brace syntax.

    Infrastructure implementation of the TemplateProcessorPort protocol.
    Provides basic template features like variable substitution, conditionals, and loops
    without requiring a full template engine like Jinja2.
    """

    # Regex patterns for different template syntaxes
    VARIABLE_PATTERN = re.compile(r"\{\{(\s*[\w\.\[\]]+\s*)\}\}")
    CONDITIONAL_PATTERN = re.compile(
        r"\{\{#(if|unless)\s+([\w\.\[\]]+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL
    )
    LOOP_PATTERN = re.compile(r"\{\{#each\s+([\w\.\[\]]+)\}\}(.*?)\{\{/each\}\}", re.DOTALL)
    SINGLE_BRACE_PATTERN = re.compile(r"\{([\w\.\[\]]+)\}")

    def process(self, template: str, context: dict[str, Any]) -> TemplateResult:
        missing_keys = []
        used_keys = []
        errors = []

        try:
            content = self._process_loops(template, context, used_keys, errors)
            content = self._process_conditionals(content, context, used_keys, errors)
            content = self._process_variables(content, context, missing_keys, used_keys)

            return TemplateResult(
                content=content,
                missing_keys=list(set(missing_keys)),
                used_keys=list(set(used_keys)),
                errors=errors,
            )
        except Exception as e:
            errors.append(f"Template processing error: {e!s}")
            return TemplateResult(
                content=template,
                missing_keys=missing_keys,
                used_keys=used_keys,
                errors=errors,
            )

    def process_simple(self, template: str, context: dict[str, Any]) -> str:
        return self.process(template, context).content

    def process_single_brace(self, template: str, context: dict[str, Any]) -> str:
        def replace_var(match):
            var_path = match.group(1)
            value = self._get_nested_value(context, var_path, context)
            return self._format_value(value) if value is not None else match.group(0)

        return self.SINGLE_BRACE_PATTERN.sub(replace_var, template)

    def extract_variables(self, template: str) -> list[str]:
        variables = []

        variables.extend(match.strip() for match in self.VARIABLE_PATTERN.findall(template))

        for match in self.CONDITIONAL_PATTERN.finditer(template):
            variables.append(match.group(2).strip())

        for match in self.LOOP_PATTERN.finditer(template):
            variables.append(match.group(1).strip())

        variables.extend(self.SINGLE_BRACE_PATTERN.findall(template))

        return sorted(list(set(variables)))

    def _process_variables(
        self, template: str, context: dict[str, Any], missing_keys: list[str], used_keys: list[str]
    ) -> str:
        def replace_var(match):
            var_path = match.group(1).strip()
            used_keys.append(var_path)

            value = self._get_nested_value(context, var_path, context)

            if value is None:
                missing_keys.append(var_path)
                return match.group(0)

            return self._format_value(value)

        return self.VARIABLE_PATTERN.sub(replace_var, template)

    def _format_value(self, value: Any) -> str:
        if isinstance(value, dict | list):
            return json.dumps(value, indent=2)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif value is None:
            return ""
        else:
            return str(value)

    def _get_nested_value(
        self, obj: dict[str, Any], path: str, root_context: dict[str, Any] | None = None
    ) -> Any:
        """Get nested value from dict using dot notation and bracket notation."""
        if root_context is None:
            root_context = obj

        if "[" in path:
            return self._resolve_path_with_indices(obj, path, root_context)

        keys = path.split(".")
        value = obj

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _resolve_path_with_indices(
        self, obj: dict[str, Any], path: str, root_context: dict[str, Any]
    ) -> Any:
        """Resolve a path that may contain array indices like 'sections[current_index].field'."""
        segments = []
        current = ""

        i = 0
        while i < len(path):
            if path[i] == "[":
                if current:
                    segments.append(current)
                    current = ""
                j = path.find("]", i)
                if j == -1:
                    return None
                segments.append(path[i : j + 1])
                i = j + 1
                if i < len(path) and path[i] == ".":
                    i += 1
            elif path[i] == ".":
                if current:
                    segments.append(current)
                    current = ""
                i += 1
            else:
                current += path[i]
                i += 1

        if current:
            segments.append(current)

        value = obj
        for segment in segments:
            if segment.startswith("[") and segment.endswith("]"):
                index_expr = segment[1:-1]

                if index_expr.isdigit():
                    index = int(index_expr)
                else:
                    index_value = self._get_nested_value(root_context, index_expr, root_context)
                    if index_value is None or not isinstance(index_value, int | str):
                        return None
                    try:
                        index = int(index_value)
                    except (ValueError, TypeError):
                        return None

                if isinstance(value, list | tuple) and 0 <= index < len(value):
                    value = value[index]
                else:
                    return None
            else:
                if isinstance(value, dict) and segment in value:
                    value = value[segment]
                else:
                    return None

        return value

    def _process_conditionals(
        self, template: str, context: dict[str, Any], used_keys: list[str], errors: list[str]
    ) -> str:
        def replace_conditional(match):
            condition_type = match.group(1)
            condition_expr = match.group(2).strip()
            block_content = match.group(3)

            used_keys.append(condition_expr)

            try:
                condition_value = self._evaluate_condition(condition_expr, context)

                if (condition_type == "if" and condition_value) or (
                    condition_type == "unless" and not condition_value
                ):
                    return block_content
                else:
                    return ""
            except Exception as e:
                errors.append(f"Conditional error in {condition_type} {condition_expr}: {e!s}")
                return match.group(0)

        return self.CONDITIONAL_PATTERN.sub(replace_conditional, template)

    def _evaluate_condition(self, expr: str, context: dict[str, Any]) -> bool:
        value = self._get_nested_value(context, expr, context)

        if value is None:
            return False
        elif isinstance(value, bool):
            return value
        elif isinstance(value, int | float):
            return value != 0
        elif isinstance(value, str):
            return value.lower() not in ("", "false", "0", "no", "none")
        elif isinstance(value, list | dict):
            return len(value) > 0
        else:
            return bool(value)

    def _process_loops(
        self, template: str, context: dict[str, Any], used_keys: list[str], errors: list[str]
    ) -> str:
        def replace_loop(match):
            items_path = match.group(1).strip()
            block_content = match.group(2)

            used_keys.append(items_path)

            items = self._get_nested_value(context, items_path, context)
            if not isinstance(items, list):
                if items is not None:
                    errors.append(f"Loop variable '{items_path}' is not a list")
                return ""

            results = []
            for i, item in enumerate(items):
                item_context = context.copy()
                item_context["this"] = item
                item_context["@index"] = i
                item_context["@first"] = i == 0
                item_context["@last"] = i == len(items) - 1

                result = self._process_variables(block_content, item_context, [], used_keys)
                results.append(result)

            return "".join(results)

        return self.LOOP_PATTERN.sub(replace_loop, template)
