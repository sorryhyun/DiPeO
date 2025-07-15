# Data transformation utilities for converting between different formats

import base64
import json
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any

import yaml


def transform_to_format(
    data: Any,
    format: str,
    options: dict[str, Any] | None = None
) -> str | bytes | dict[str, Any]:
    # Transform data to specified format
    options = options or {}
    
    if format == 'json':
        return _to_json(data, options)
    elif format == 'yaml':
        return _to_yaml(data, options)
    elif format == 'xml':
        return _to_xml(data, options)
    elif format == 'form':
        return _to_form_data(data, options)
    elif format == 'csv':
        return _to_csv(data, options)
    elif format == 'base64':
        return _to_base64(data, options)
    else:
        raise ValueError(f"Unsupported format: {format}")


def transform_from_format(
    data: str | bytes,
    format: str,
    options: dict[str, Any] | None = None
) -> Any:
    # Transform data from specified format
    options = options or {}
    
    if format == 'json':
        return _from_json(data, options)
    elif format == 'yaml':
        return _from_yaml(data, options)
    elif format == 'xml':
        return _from_xml(data, options)
    elif format == 'form':
        return _from_form_data(data, options)
    elif format == 'csv':
        return _from_csv(data, options)
    elif format == 'base64':
        return _from_base64(data, options)
    else:
        raise ValueError(f"Unsupported format: {format}")


def _to_json(data: Any, options: dict[str, Any]) -> str:
    # Convert data to JSON
    indent = options.get('indent', 2) if options.get('pretty', True) else None
    
    # Custom JSON encoder for special types
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, bytes):
                return base64.b64encode(obj).decode('utf-8')
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return super().default(obj)
    
    return json.dumps(data, indent=indent, cls=CustomEncoder)


def _from_json(data: str | bytes, options: dict[str, Any]) -> Any:
    # Parse JSON data
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return json.loads(data)


def _to_yaml(data: Any, options: dict[str, Any]) -> str:
    # Convert data to YAML
    # Simple YAML serialization
    def serialize_value(value, indent=0):
        spaces = '  ' * indent
        
        if isinstance(value, dict):
            lines = []
            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{spaces}{k}:")
                    lines.append(serialize_value(v, indent + 1))
                else:
                    lines.append(f"{spaces}{k}: {serialize_value(v)}")
            return '\n'.join(lines)
        elif isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{spaces}- ")
                    lines.append(serialize_value(item, indent + 1))
                else:
                    lines.append(f"{spaces}- {serialize_value(item)}")
            return '\n'.join(lines)
        elif isinstance(value, str):
            if '\n' in value or '"' in value or "'" in value:
                return f'"{value.replace('"', '\\"')}"'
            return value
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif value is None:
            return 'null'
        else:
            return str(value)
    
    return serialize_value(data)


def _from_yaml(data: str | bytes, options: dict[str, Any]) -> Any:
    # Parse YAML data
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    # For full YAML support, would use PyYAML
    # This is a simplified version
    return yaml.safe_load(data) if yaml else json.loads(data)


def _to_xml(data: Any, options: dict[str, Any]) -> str:
    # Convert data to XML
    root_tag = options.get('root_tag', 'root')
    
    def build_element(parent, key, value):
        if isinstance(value, dict):
            elem = ET.SubElement(parent, key)
            for k, v in value.items():
                build_element(elem, k, v)
        elif isinstance(value, list):
            for item in value:
                build_element(parent, key, item)
        else:
            elem = ET.SubElement(parent, key)
            elem.text = str(value)
    
    root = ET.Element(root_tag)
    
    if isinstance(data, dict):
        for key, value in data.items():
            build_element(root, key, value)
    else:
        root.text = str(data)
    
    return ET.tostring(root, encoding='unicode')


def _from_xml(data: str | bytes, options: dict[str, Any]) -> dict[str, Any]:
    # Parse XML data
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    
    root = ET.fromstring(data)
    
    def parse_element(element):
        result = {}
        
        # Handle attributes
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Handle text content
        if element.text and element.text.strip():
            if len(element) == 0:  # No children
                return element.text.strip()
            else:
                result['#text'] = element.text.strip()
        
        # Handle children
        for child in element:
            child_data = parse_element(child)
            if child.tag in result:
                # Convert to list if multiple elements with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result if result else None
    
    return {root.tag: parse_element(root)}


def _to_form_data(data: dict[str, Any], options: dict[str, Any]) -> str:
    # Convert data to form-encoded format
    from urllib.parse import urlencode
    
    # Flatten nested structures
    flat_data = {}
    
    def flatten(obj, prefix=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}[{key}]" if prefix else key
                flatten(value, new_key)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                new_key = f"{prefix}[{i}]"
                flatten(value, new_key)
        else:
            flat_data[prefix] = str(obj)
    
    flatten(data)
    return urlencode(flat_data)


def _from_form_data(data: str | bytes, options: dict[str, Any]) -> dict[str, Any]:
    # Parse form-encoded data
    from urllib.parse import parse_qs
    
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    
    parsed = parse_qs(data)
    # parse_qs returns lists for all values, simplify when single value
    result = {}
    for key, values in parsed.items():
        result[key] = values[0] if len(values) == 1 else values
    
    return result


def _to_csv(data: list[dict[str, Any]], options: dict[str, Any]) -> str:
    # Convert data to CSV
    if not isinstance(data, list):
        raise ValueError("CSV format requires a list of dictionaries")
    
    if not data:
        return ""
    
    # Get headers from first item
    headers = list(data[0].keys())
    delimiter = options.get('delimiter', ',')
    
    lines = []
    # Add header row
    lines.append(delimiter.join(headers))
    
    # Add data rows
    for row in data:
        values = []
        for header in headers:
            value = str(row.get(header, ''))
            # Quote values containing delimiter or quotes
            if delimiter in value or '"' in value or '\n' in value:
                value = f'"{value.replace('"', '""')}"'
            values.append(value)
        lines.append(delimiter.join(values))
    
    return '\n'.join(lines)


def _from_csv(data: str | bytes, options: dict[str, Any]) -> list[dict[str, Any]]:
    # Parse CSV data
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    
    delimiter = options.get('delimiter', ',')
    lines = data.strip().split('\n')
    
    if not lines:
        return []
    
    # Parse header
    headers = [h.strip() for h in lines[0].split(delimiter)]
    
    # Parse rows
    result = []
    for line in lines[1:]:
        if not line.strip():
            continue
        
        # Simple CSV parsing (for full support, use csv module)
        values = line.split(delimiter)
        row = {}
        for i, header in enumerate(headers):
            if i < len(values):
                value = values[i].strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1].replace('""', '"')
                row[header] = value
            else:
                row[header] = ''
        result.append(row)
    
    return result


def _to_base64(data: str | bytes, options: dict[str, Any]) -> str:
    # Convert data to base64
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('ascii')


def _from_base64(data: str | bytes, options: dict[str, Any]) -> bytes:
    # Decode base64 data
    if isinstance(data, bytes):
        data = data.decode('ascii')
    return base64.b64decode(data)


def apply_transformation_chain(
    data: Any,
    transformations: list[dict[str, Any]]
) -> Any:
    # Apply a chain of transformations to data
    result = data
    
    for transform in transformations:
        transform_type = transform.get('type')
        options = transform.get('options', {})
        
        if transform_type == 'format':
            from_format = transform.get('from')
            to_format = transform.get('to')
            
            if from_format:
                result = transform_from_format(result, from_format, options)
            if to_format:
                result = transform_to_format(result, to_format, options)
        
        elif transform_type == 'jq':
            # Would use jq-like transformations
            pass
        
        elif transform_type == 'custom':
            # Custom transformation function
            pass
    
    return result