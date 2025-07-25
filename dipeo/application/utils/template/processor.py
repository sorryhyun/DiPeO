# Unified template processor combining all template features

import json
import re
from datetime import datetime
from typing import Any

from .types import TemplateResult


class TemplateProcessor:
    # Unified template processor supporting Handlebars-style syntax
    
    # Regex patterns for different template syntaxes
    VARIABLE_PATTERN = re.compile(r'\{\{(\s*[\w\.]+\s*)\}\}')
    CONDITIONAL_PATTERN = re.compile(r'\{\{#(if|unless)\s+([\w\.]+)\}\}(.*?)\{\{/\1\}\}', re.DOTALL)
    LOOP_PATTERN = re.compile(r'\{\{#each\s+([\w\.]+)\}\}(.*?)\{\{/each\}\}', re.DOTALL)
    SINGLE_BRACE_PATTERN = re.compile(r'\{([\w\.]+)\}')  # For arrow transformations, supports dot notation
    
    def process(self, template: str, context: dict[str, Any]) -> TemplateResult:
        # Process template and return detailed result
        missing_keys = []
        used_keys = []
        errors = []
        
        try:
            # Process in order: loops -> conditionals -> variables
            content = self._process_loops(template, context, used_keys, errors)
            content = self._process_conditionals(content, context, used_keys, errors)
            content = self._process_variables(content, context, missing_keys, used_keys)
            
            return TemplateResult(
                content=content,
                missing_keys=list(set(missing_keys)),
                used_keys=list(set(used_keys)),
                errors=errors
            )
        except Exception as e:
            errors.append(f"Template processing error: {e!s}")
            return TemplateResult(
                content=template,  # Always return original on error
                missing_keys=missing_keys,
                used_keys=used_keys,
                errors=errors
            )
    
    def process_simple(self, template: str, context: dict[str, Any]) -> str:
        # Convenience method that returns just the processed content
        return self.process(template, context).content
    
    def _process_variables(
        self,
        template: str,
        context: dict[str, Any],
        missing_keys: list[str],
        used_keys: list[str]
    ) -> str:
        # Process variable substitutions
        def replace_var(match):
            var_path = match.group(1).strip()
            used_keys.append(var_path)
            
            value = self._get_nested_value(context, var_path)
            
            if value is None:
                missing_keys.append(var_path)
                return match.group(0)  # Keep original on missing
            
            return self._format_value(value)
        
        return self.VARIABLE_PATTERN.sub(replace_var, template)
    
    def process_single_brace(self, template: str, context: dict[str, Any]) -> str:
        # Process single brace variables (for arrow transformations)
        def replace_var(match):
            var_path = match.group(1)
            # Support nested values with dot notation
            value = self._get_nested_value(context, var_path)
            return self._format_value(value) if value is not None else match.group(0)
        
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
        errors: list[str]
    ) -> str:
        # Process conditional blocks
        def replace_conditional(match):
            condition_type = match.group(1)  # 'if' or 'unless'
            condition_expr = match.group(2).strip()
            block_content = match.group(3)
            
            used_keys.append(condition_expr)
            
            try:
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
        errors: list[str]
    ) -> str:
        # Process loop blocks
        def replace_loop(match):
            items_path = match.group(1).strip()
            block_content = match.group(2)
            
            used_keys.append(items_path)
            
            items = self._get_nested_value(context, items_path)
            if not isinstance(items, list):
                if items is not None:
                    errors.append(f"Loop variable '{items_path}' is not a list")
                return ''
            
            results = []
            for i, item in enumerate(items):
                # Create item context with loop variables
                item_context = context.copy()
                item_context['this'] = item
                item_context['@index'] = i
                item_context['@first'] = i == 0
                item_context['@last'] = i == len(items) - 1
                
                # Process content with item context (don't track missing keys in loops)
                result = self._process_variables(block_content, item_context, [], used_keys)
                results.append(result)
            
            return ''.join(results)
        
        return self.LOOP_PATTERN.sub(replace_loop, template)
    
    def extract_variables(self, template: str) -> list[str]:
        # Extract all variable names from a template
        variables = []
        
        # Find all {{variable}} patterns
        variables.extend(match.strip() for match in self.VARIABLE_PATTERN.findall(template))
        
        # Find variables in conditionals
        for match in self.CONDITIONAL_PATTERN.finditer(template):
            variables.append(match.group(2).strip())
        
        # Find variables in loops  
        for match in self.LOOP_PATTERN.finditer(template):
            variables.append(match.group(1).strip())
        
        # Find single brace variables
        variables.extend(self.SINGLE_BRACE_PATTERN.findall(template))
        
        return sorted(list(set(variables)))