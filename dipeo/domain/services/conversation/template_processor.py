"""Template processing for conversation messages."""

from typing import Dict, Any, List, Optional
import re
import json
from datetime import datetime


class TemplateProcessor:
    """Processes templates for conversation messages."""
    
    @staticmethod
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
            value = TemplateProcessor._get_nested_value(context, var_name)
            
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
    
    @staticmethod
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
    
    @staticmethod
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
        template = TemplateProcessor._process_if_conditions(template, context)
        
        # Process unless conditions
        template = TemplateProcessor._process_unless_conditions(template, context)
        
        # Process each loops
        template = TemplateProcessor._process_each_loops(template, context)
        
        # Process regular variables
        return TemplateProcessor.process_template(template, context)
    
    @staticmethod
    def _process_if_conditions(template: str, context: Dict[str, Any]) -> str:
        """Process {{#if}} conditions."""
        pattern = r'\{\{#if\s+([\w\.]+)\}\}(.*?)\{\{/if\}\}'
        
        def replacer(match):
            condition = match.group(1)
            content = match.group(2)
            
            value = TemplateProcessor._get_nested_value(context, condition)
            if value:
                return content
            return ''
        
        return re.sub(pattern, replacer, template, flags=re.DOTALL)
    
    @staticmethod
    def _process_unless_conditions(template: str, context: Dict[str, Any]) -> str:
        """Process {{#unless}} conditions."""
        pattern = r'\{\{#unless\s+([\w\.]+)\}\}(.*?)\{\{/unless\}\}'
        
        def replacer(match):
            condition = match.group(1)
            content = match.group(2)
            
            value = TemplateProcessor._get_nested_value(context, condition)
            if not value:
                return content
            return ''
        
        return re.sub(pattern, replacer, template, flags=re.DOTALL)
    
    @staticmethod
    def _process_each_loops(template: str, context: Dict[str, Any]) -> str:
        """Process {{#each}} loops."""
        pattern = r'\{\{#each\s+([\w\.]+)\}\}(.*?)\{\{/each\}\}'
        
        def replacer(match):
            items_path = match.group(1)
            content = match.group(2)
            
            items = TemplateProcessor._get_nested_value(context, items_path)
            if not isinstance(items, list):
                return ''
            
            results = []
            for i, item in enumerate(items):
                item_context = context.copy()
                item_context['this'] = item
                item_context['index'] = i
                
                # Process the content for this item
                processed = TemplateProcessor.process_template(content, item_context)
                results.append(processed)
            
            return ''.join(results)
        
        return re.sub(pattern, replacer, template, flags=re.DOTALL)
    
    @staticmethod
    def extract_variables(template: str) -> List[str]:
        """Extract all variable names from a template."""
        pattern = r'\{\{(\s*[\w\.]+\s*)\}\}'
        matches = re.findall(pattern, template)
        return [match.strip() for match in matches]
    
    @staticmethod
    def validate_template(template: str) -> List[str]:
        """Validate template syntax and return errors."""
        errors = []
        
        # Check for unclosed variables
        open_count = template.count('{{')
        close_count = template.count('}}')
        if open_count != close_count:
            errors.append(f"Unmatched template brackets: {open_count} opens, {close_count} closes")
        
        # Check for unclosed conditionals
        for tag in ['if', 'unless', 'each']:
            open_pattern = f'{{{{#{tag}'
            close_pattern = f'{{{{/{tag}}}}}'
            open_tags = len(re.findall(open_pattern, template))
            close_tags = len(re.findall(close_pattern, template))
            if open_tags != close_tags:
                errors.append(f"Unmatched {tag} blocks: {open_tags} opens, {close_tags} closes")
        
        return errors
    
    @staticmethod
    def create_template_context(
        inputs: Dict[str, Any],
        outputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a standard context for template processing."""
        context = {
            'inputs': inputs,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        if outputs:
            context['outputs'] = outputs
        
        if metadata:
            context['metadata'] = metadata
        
        # Add some utility values
        context['date'] = datetime.utcnow().strftime('%Y-%m-%d')
        context['time'] = datetime.utcnow().strftime('%H:%M:%S')
        
        # Flatten common inputs to top level for convenience
        for key, value in inputs.items():
            if key not in context and isinstance(key, str) and key.isidentifier():
                context[key] = value
        
        return context