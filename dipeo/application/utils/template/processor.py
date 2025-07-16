# Unified template processor combining all template features

import json
import re
import warnings
from datetime import datetime
from typing import Any

from .types import TemplateResult


class TemplateProcessor:
    # Unified template processor combining all existing features
    
    # Regex patterns - supporting various syntax variations found in codebase
    VARIABLE_PATTERN = re.compile(r'\{\{(\s*[\w\.]+\s*)\}\}')
    CONDITIONAL_PATTERN = re.compile(r'\{\{#(if|unless)\s+([\w\.]+)\}\}(.*?)\{\{/\1\}\}', re.DOTALL)
    LOOP_PATTERN = re.compile(r'\{\{#each\s+([\w\.]+)\}\}(.*?)\{\{/each\}\}', re.DOTALL)
    # Support single brace syntax for arrow transformations
    SINGLE_BRACE_PATTERN = re.compile(r'\{(\w+)\}')
    
    def process(
        self,
        template: str,
        context: dict[str, Any],
        safe: bool = True,
        track_usage: bool = True
    ) -> TemplateResult:
        # Process template with full feature support
        missing_keys = []
        used_keys = []
        errors = []
        
        # Validate template first
        validation_errors = self.validate_template(template)
        if validation_errors:
            errors.extend(validation_errors)
            if not safe:
                return TemplateResult(
                    content="",
                    missing_keys=missing_keys,
                    used_keys=used_keys,
                    errors=errors
                )
        
        try:
            # Process in order: loops -> conditionals -> variables
            content = self._process_loops(template, context, used_keys, errors, track_usage)
            content = self._process_conditionals(content, context, used_keys, errors, track_usage)
            content = self._process_variables(content, context, missing_keys, used_keys, safe, track_usage)
            
            return TemplateResult(
                content=content,
                missing_keys=list(set(missing_keys)),  # Remove duplicates
                used_keys=list(set(used_keys)),
                errors=errors
            )
        except Exception as e:
            errors.append(f"Template processing error: {e!s}")
            return TemplateResult(
                content=template if safe else "",
                missing_keys=missing_keys,
                used_keys=used_keys,
                errors=errors
            )
    
    def process_simple(self, template: str, context: dict[str, Any]) -> str:
        # Simple processing that returns just the content
        result = self.process(template, context)
        return result.content
    
    def _process_variables(
        self,
        template: str,
        context: dict[str, Any],
        missing_keys: list[str],
        used_keys: list[str],
        safe: bool,
        track_usage: bool
    ) -> str:
        # Process variable substitutions
        def replace_var(match):
            var_path = match.group(1).strip()
            if track_usage:
                used_keys.append(var_path)
            
            value = self._get_nested_value(context, var_path)
            
            if value is None:
                if track_usage:
                    missing_keys.append(var_path)
                return match.group(0) if safe else ""
            
            # Format value based on type
            return self._format_value(value)
        
        return self.VARIABLE_PATTERN.sub(replace_var, template)
    
    def _process_single_brace_variables(
        self,
        template: str,
        context: dict[str, Any],
        safe: bool = True
    ) -> str:
        # Process single brace variables for arrow transformations
        def replace_var(match):
            var_name = match.group(1)
            value = context.get(var_name)
            
            if value is None:
                return match.group(0) if safe else ""
            
            return self._format_value(value)
        
        return self.SINGLE_BRACE_PATTERN.sub(replace_var, template)
    
    def _format_value(self, value: Any) -> str:
        # Format value based on type
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif value is None:
            return ""
        else:
            return str(value)
    
    def _get_nested_value(self, obj: dict[str, Any], path: str) -> Any:
        # Get nested value from dict using dot notation
        keys = path.split('.')
        value = obj
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _process_conditionals(
        self,
        template: str,
        context: dict[str, Any],
        used_keys: list[str],
        errors: list[str],
        track_usage: bool
    ) -> str:
        # Process conditional blocks
        def replace_conditional(match):
            condition_type = match.group(1)  # 'if' or 'unless'
            condition_expr = match.group(2).strip()
            block_content = match.group(3)
            
            if track_usage:
                used_keys.append(condition_expr)
            
            try:
                # Evaluate condition
                condition_value = self._evaluate_condition(condition_expr, context)
                
                if (condition_type == 'if' and condition_value) or (condition_type == 'unless' and not condition_value):
                    return block_content
                else:
                    return ''
            except Exception as e:
                errors.append(f"Conditional error in {condition_type} {condition_expr}: {e!s}")
                return match.group(0)
        
        return self.CONDITIONAL_PATTERN.sub(replace_conditional, template)
    
    def _evaluate_condition(self, expr: str, context: dict[str, Any]) -> bool:
        # Safely evaluate a condition expression
        value = self._get_nested_value(context, expr)
        
        # Handle various truthy values
        if value is None:
            return False
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return value.lower() not in ('', 'false', '0', 'no', 'none')
        elif isinstance(value, (list, dict)):
            return len(value) > 0
        else:
            return bool(value)
    
    def _process_loops(
        self,
        template: str,
        context: dict[str, Any],
        used_keys: list[str],
        errors: list[str],
        track_usage: bool
    ) -> str:
        # Process loop blocks
        def replace_loop(match):
            items_path = match.group(1).strip()
            block_content = match.group(2)
            
            if track_usage:
                used_keys.append(items_path)
            
            items = self._get_nested_value(context, items_path)
            if not isinstance(items, list):
                if items is not None:
                    errors.append(f"Loop variable '{items_path}' is not a list")
                return ''
            
            results = []
            for i, item in enumerate(items):
                # Create item context
                item_context = context.copy()
                item_context['this'] = item
                item_context['@index'] = i
                item_context['@first'] = i == 0
                item_context['@last'] = i == len(items) - 1
                
                # Process content with item context
                result = self._process_variables(
                    block_content, 
                    item_context,
                    [],  # Don't track missing keys in loops
                    used_keys if track_usage else [],
                    True,  # Always safe mode in loops
                    track_usage
                )
                results.append(result)
            
            return ''.join(results)
        
        return self.LOOP_PATTERN.sub(replace_loop, template)
    
    def extract_variables(self, template: str) -> list[str]:
        # Extract all variable names from a template
        variables = []
        
        # Find all {{variable}} patterns
        matches = self.VARIABLE_PATTERN.findall(template)
        variables.extend(match.strip() for match in matches)
        
        # Find variables in conditionals
        for match in self.CONDITIONAL_PATTERN.finditer(template):
            variables.append(match.group(2).strip())
        
        # Find variables in loops
        for match in self.LOOP_PATTERN.finditer(template):
            variables.append(match.group(1).strip())
        
        # Find single brace variables
        matches = self.SINGLE_BRACE_PATTERN.findall(template)
        variables.extend(matches)
        
        # Clean and deduplicate
        return sorted(list(set(variables)))
    
    def validate_template(self, template: str) -> list[str]:
        # Validate template syntax and return any errors
        errors = []
        
        # Check for unclosed variables
        open_count = template.count('{{')
        close_count = template.count('}}')
        if open_count != close_count:
            errors.append(f"Mismatched braces: {open_count} opening, {close_count} closing")
        
        # Check for unclosed if blocks
        if_opens = len(re.findall(r'\{\{#if\s+[\w\.]+\}\}', template))
        if_closes = len(re.findall(r'\{\{/if\}\}', template))
        if if_opens != if_closes:
            errors.append(f"Mismatched if blocks: {if_opens} opening, {if_closes} closing")
        
        # Check for unclosed unless blocks
        unless_opens = len(re.findall(r'\{\{#unless\s+[\w\.]+\}\}', template))
        unless_closes = len(re.findall(r'\{\{/unless\}\}', template))
        if unless_opens != unless_closes:
            errors.append(f"Mismatched unless blocks: {unless_opens} opening, {unless_closes} closing")
        
        # Check for unclosed each blocks
        each_opens = len(re.findall(r'\{\{#each\s+[\w\.]+\}\}', template))
        each_closes = len(re.findall(r'\{\{/each\}\}', template))
        if each_opens != each_closes:
            errors.append(f"Mismatched each blocks: {each_opens} opening, {each_closes} closing")
        
        return errors
    
    def create_context(
        self,
        variables: dict[str, Any],
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        # Create a context dictionary for template processing
        context = variables.copy()
        
        if metadata:
            context['_metadata'] = metadata
        
        # Add utility values
        context['_timestamp'] = datetime.utcnow().isoformat()
        
        return context


# Backward compatibility functions (delegating to processor instance)
_default_processor = TemplateProcessor()


def process_template(template: str, context: dict[str, Any], safe: bool = True) -> str:
    # Process a template string with context values
    return _default_processor.process(template, context, safe=safe).content


def process_conditional_template(template: str, context: dict[str, Any]) -> str:
    # Process template with conditional sections
    return _default_processor.process(template, context).content


def extract_variables(template: str) -> list[str]:
    # Extract all variable names from a template
    return _default_processor.extract_variables(template)


def validate_template(template: str) -> list[str]:
    # Validate template syntax
    return _default_processor.validate_template(template)


def create_template_context(
    variables: dict[str, Any],
    metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    # Create a context dictionary
    return _default_processor.create_context(variables, metadata)


# Legacy TemplateService for backward compatibility
class TemplateService:
    # Legacy TemplateService API for backward compatibility
    
    def __init__(self):
        self._processor = TemplateProcessor()
        self._deprecation_warned = False
        # Legacy state tracking
        self.missing_keys: list[str] = []
        self.used_keys: list[str] = []
    
    def _warn_deprecation(self):
        if not self._deprecation_warned:
            warnings.warn(
                "TemplateService is deprecated. Use TemplateProcessor directly.",
                DeprecationWarning,
                stacklevel=3
            )
            self._deprecation_warned = True
    
    def substitute(
        self,
        template: str,
        values: dict[str, Any],
        track_usage: bool = True
    ) -> str:
        # Legacy substitute method
        self._warn_deprecation()
        result = self._processor.process(template, values, track_usage=track_usage)
        
        # Store state for legacy access
        self.missing_keys = result.missing_keys
        self.used_keys = result.used_keys
        
        return result.content
    
    def process_template(self, template: str, values: dict[str, Any]) -> str:
        # Alternative legacy method name
        return self.substitute(template, values)