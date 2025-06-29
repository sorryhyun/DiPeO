#!/usr/bin/env node
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

// Types
interface Property {
  name: string;
  type: string;
  optional?: boolean;
  description?: string;
}

interface TypeDef {
  name: string;
  type: 'interface' | 'enum' | 'type';
  properties?: Property[];
  values?: string[];
  value?: string;
}

const DTO_HEADER = `"""
Generated DTOs for application layer.
DO NOT EDIT DIRECTLY - Generated from TypeScript domain models.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any, NewType
from enum import Enum
from datetime import datetime

`;

// Map TypeScript types to Python types for DTOs
function mapTypeToPython(tsType: string): string {
  const typeMap: Record<string, string> = {
    'string': 'str',
    'number': 'float',
    'boolean': 'bool',
    'any': 'Any',
    'Date': 'datetime',
    'unknown': 'Any',
    'null': 'None',
    'undefined': 'None',
  };

  // Handle arrays
  if (tsType.endsWith('[]')) {
    const innerType = tsType.slice(0, -2);
    return `List[${mapTypeToPython(innerType)}]`;
  }

  // Handle Record types
  if (tsType.startsWith('Record<')) {
    const match = tsType.match(/Record<(\w+),\s*(.+)>/);
    if (match) {
      const keyType = mapTypeToPython(match[1]);
      const valueType = mapTypeToPython(match[2]);
      return `Dict[${keyType}, ${valueType}]`;
    }
  }

  // Handle union types
  if (tsType.includes('|')) {
    const types = tsType.split('|').map(t => mapTypeToPython(t.trim()));
    if (types.length === 2 && types.includes('None')) {
      const nonNoneType = types.find(t => t !== 'None');
      return `Optional[${nonNoneType}]`;
    }
    return `Union[${types.join(', ')}]`;
  }

  // Handle literal types
  if (tsType.startsWith('"') && tsType.endsWith('"')) {
    return `'${tsType.slice(1, -1)}'`;
  }

  return typeMap[tsType] || tsType;
}

// Generate Python DTO from TypeDef
function generateDTO(typeDef: TypeDef, suffix: string = 'DTO'): string {
  if (typeDef.type === 'enum') {
    let result = `class ${typeDef.name}${suffix}(str, Enum):\n`;
    typeDef.values?.forEach(value => {
      const pythonName = value.toUpperCase();
      result += `    ${pythonName} = "${value}"\n`;
    });
    return result + '\n';
  }

  if (typeDef.type === 'type' && typeDef.value) {
    // For branded types, create simple aliases
    if (typeDef.value === 'string') {
      return `${typeDef.name}${suffix} = str\n`;
    }
    return `${typeDef.name}${suffix} = ${mapTypeToPython(typeDef.value)}\n`;
  }

  // Generate dataclass for interfaces
  let result = `@dataclass\nclass ${typeDef.name}${suffix}:\n`;
  
  if (!typeDef.properties || typeDef.properties.length === 0) {
    result += '    pass\n';
    return result + '\n';
  }

  // First, add all required fields
  const requiredFields = typeDef.properties.filter(p => !p.optional);
  const optionalFields = typeDef.properties.filter(p => p.optional);

  if (requiredFields.length === 0 && optionalFields.length > 0) {
    result += '    pass\n';
  }

  requiredFields.forEach(prop => {
    const pythonType = mapTypeToPython(prop.type);
    const pythonName = camelToSnake(prop.name);
    result += `    ${pythonName}: ${pythonType}\n`;
  });

  // Then add optional fields with defaults
  optionalFields.forEach(prop => {
    const pythonType = mapTypeToPython(prop.type);
    const pythonName = camelToSnake(prop.name);
    
    if (pythonType.startsWith('List[')) {
      result += `    ${pythonName}: ${pythonType} = field(default_factory=list)\n`;
    } else if (pythonType.startsWith('Dict[')) {
      result += `    ${pythonName}: ${pythonType} = field(default_factory=dict)\n`;
    } else {
      result += `    ${pythonName}: Optional[${pythonType}] = None\n`;
    }
  });

  return result + '\n';
}

// Convert camelCase to snake_case
function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`).replace(/^_/, '');
}

// Parse schema and generate DTOs
function generateDTOs(schemaPath: string): string {
  const schemaArray = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));
  let output = DTO_HEADER;
  
  // Categorize types for DTO generation
  const dtoCategories = {
    request: [] as TypeDef[],
    response: [] as TypeDef[],
    common: [] as TypeDef[],
    events: [] as TypeDef[],
  };

  // Process all types
  schemaArray.forEach((def: any) => {
    // Convert properties object to array format
    let properties: Property[] = [];
    if (def.properties && typeof def.properties === 'object') {
      properties = Object.entries(def.properties).map(([name, prop]: [string, any]) => ({
        name,
        type: prop.type.replace(/import\([^)]+\)\./, ''), // Clean import paths
        optional: prop.optional,
        description: prop.description,
      }));
    }

    const typeDef: TypeDef = {
      name: def.name,
      type: def.type || 'interface',
      properties,
      values: def.values,
      value: def.value,
    };

    // Categorize based on name patterns
    if (def.name.includes('Input') || def.name.includes('Create') || def.name.includes('Update')) {
      dtoCategories.request.push(typeDef);
    } else if (def.name.includes('Result') || def.name.includes('Response')) {
      dtoCategories.response.push(typeDef);
    } else if (def.name.includes('Event') || def.name.includes('Message')) {
      dtoCategories.events.push(typeDef);
    } else {
      dtoCategories.common.push(typeDef);
    }
  });

  // Generate DTOs by category
  output += '# Common DTOs\n';
  dtoCategories.common.forEach(typeDef => {
    output += generateDTO(typeDef, '');
  });

  output += '\n# Request DTOs\n';
  dtoCategories.request.forEach(typeDef => {
    output += generateDTO(typeDef, 'Request');
  });

  output += '\n# Response DTOs\n';
  dtoCategories.response.forEach(typeDef => {
    output += generateDTO(typeDef, 'Response');
  });

  output += '\n# Event DTOs\n';
  dtoCategories.events.forEach(typeDef => {
    output += generateDTO(typeDef, 'Event');
  });

  // Add utility functions for ID generation
  output += `
# Utility functions
def generate_id(prefix: str) -> str:
    """Generate a unique ID with the given prefix."""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def generate_node_id() -> str:
    return generate_id("node")

def generate_diagram_id() -> str:
    return generate_id("diagram")

def generate_person_id() -> str:
    return generate_id("person")
`;

  return output;
}

// Main execution
async function main() {
  const projectRoot = path.resolve(__dirname, '../../..');
  const schemaPath = path.join(__dirname, '../__generated__/schemas.json');
  const outputPath = path.join(
    projectRoot,
    'packages/python/dipeo_application/src/dipeo_application/dto/__generated__.py'
  );

  console.log('Generating Python DTOs for application layer...');

  // Ensure schema exists
  if (!fs.existsSync(schemaPath)) {
    console.error('Schema file not found. Running schema generation first...');
    execSync('pnpm run generate:schema', { cwd: path.join(__dirname, '..') });
  }

  // Ensure output directory exists
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Generate DTOs
  const dtoContent = generateDTOs(schemaPath);
  
  // Write output
  fs.writeFileSync(outputPath, dtoContent);
  console.log(`✅ Generated DTOs at ${outputPath}`);

  // Create __init__.py if it doesn't exist
  const initPath = path.join(outputDir, '__init__.py');
  if (!fs.existsSync(initPath)) {
    fs.writeFileSync(initPath, '"""Application layer DTOs."""\nfrom .generated import *\n');
  }
}

// Run
main().catch(console.error);