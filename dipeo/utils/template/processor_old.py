"""Template processing utilities for conversation messages.

Pure functions for template string processing, variable substitution,
and conditional template evaluation.
"""

from typing import Dict, Any, List, Optional
import re
import json
from datetime import datetime


def process_template(
    template: str,
    context: Dict[str, Any],
    safe: bool = True
) -> str:
    """Process a template string with context values.
    
    Args:
        template: Template string with {{variable}} placeholders
        context: Dictionary of values to substitute
        safe: If True, missing variables are left as-is
        
    Returns:
        Processed template string
    """
    # Find all template variables
    pattern = r'\{\{(\s*[\w\.]+\s*)\}\}'
    
    def replacer(match):
        var_name = match.group(1).strip()
        value = _get_nested_value(context, var_name)
        
        if value is None and safe:
            return match.group(0)  # Keep original placeholder
        
        # Format value based on type
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        elif isinstance(value, datetime):
            return value.isoformat()
        else:
            return str(value)
    
    return re.sub(pattern, replacer, template)


def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get value from nested dictionary using dot notation."""
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    
    return current


def process_conditional_template(
    template: str,
    context: Dict[str, Any]
) -> str:
    """Process template with conditional sections.
    
    Supports:
    - {{#if condition}}...{{/if}}
    - {{#unless condition}}...{{/unless}}
    - {{#each items}}...{{/each}}
    """
    # Process if conditions
    template = _process_if_conditions(template, context)
    
    # Process unless conditions
    template = _process_unless_conditions(template, context)
    
    # Process each loops
    template = _process_each_loops(template, context)
    
    # Process regular variables
    return process_template(template, context)


def _process_if_conditions(template: str, context: Dict[str, Any]) -> str:
    """Process {{#if}} conditions."""
    pattern = r'\{\{#if\s+([\w\.]+)\}\}(.*?)\{\{/if\}\}'
    
    def replacer(match):
        condition = match.group(1)
        content = match.group(2)
        
        value = _get_nested_value(context, condition)
        if value:
            return content
        return ''
    
    return re.sub(pattern, replacer, template, flags=re.DOTALL)


def _process_unless_conditions(template: str, context: Dict[str, Any]) -> str:
    """Process {{#unless}} conditions."""
    pattern = r'\{\{#unless\s+([\w\.]+)\}\}(.*?)\{\{/unless\}\}'
    
    def replacer(match):
        condition = match.group(1)
        content = match.group(2)
        
        value = _get_nested_value(context, condition)
        if not value:
            return content
        return ''
    
    return re.sub(pattern, replacer, template, flags=re.DOTALL)


def _process_each_loops(template: str, context: Dict[str, Any]) -> str:
    """Process {{#each}} loops."""
    pattern = r'\{\{#each\s+([\w\.]+)\}\}(.*?)\{\{/each\}\}'
    
    def replacer(match):
        items_path = match.group(1)
        content = match.group(2)
        
        items = _get_nested_value(context, items_path)
        if not isinstance(items, list):
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
            result = process_template(content, item_context)
            results.append(result)
        
        return ''.join(results)
    
    return re.sub(pattern, replacer, template, flags=re.DOTALL)


def extract_variables(template: str) -> List[str]:
    """Extract all variable names from a template.
    
    Args:
        template: Template string
        
    Returns:
        List of unique variable names found in template
    """
    # Find all {{variable}} patterns
    pattern = r'\{\{(\s*[\w\.]+\s*)\}\}'
    matches = re.findall(pattern, template)
    
    # Also find variables in conditionals
    if_pattern = r'\{\{#if\s+([\w\.]+)\}\}'
    unless_pattern = r'\{\{#unless\s+([\w\.]+)\}\}'
    each_pattern = r'\{\{#each\s+([\w\.]+)\}\}'
    
    matches.extend(re.findall(if_pattern, template))
    matches.extend(re.findall(unless_pattern, template))
    matches.extend(re.findall(each_pattern, template))
    
    # Clean and deduplicate
    variables = list(set(match.strip() for match in matches))
    return sorted(variables)


def validate_template(template: str) -> List[str]:
    """Validate template syntax and return any errors.
    
    Args:
        template: Template string to validate
        
    Returns:
        List of error messages (empty if valid)
    """
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


def create_template_context(
    variables: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a context dictionary for template processing.
    
    Args:
        variables: User variables
        metadata: Optional metadata to include
        
    Returns:
        Combined context dictionary
    """
    context = variables.copy()
    
    if metadata:
        context['_metadata'] = metadata
    
    # Add utility values
    context['_timestamp'] = datetime.utcnow().isoformat()
    
    return context