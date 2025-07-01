#!/usr/bin/env node
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';

// Define __dirname for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

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
from typing import List, Dict, Optional, Union, Any, Type, TYPE_CHECKING
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator

from dipeo_application.dto.base import (
    BaseDTO, ConvertibleDTO, RequestDTO, ResponseDTO,
    PaginatedResponseDTO, ListRequestDTO, BatchRequestDTO, BatchResponseDTO
)

# Import domain types that are referenced in DTOs
from dipeo_domain.models import (
    # IDs
    NodeID, ArrowID, HandleID, PersonID, ApiKeyID, DiagramID, ExecutionID,
    # Conversation types
    Message, MemoryConfig, MemoryState, Vec2,
    # Enums  
    HandleDirection, NodeType, DataType, ForgettingMode, DiagramFormat,
    DBBlockSubType, ContentType, SupportedLanguage, ExecutionStatus,
    NodeExecutionStatus, EventType, LLMService, NotionOperation,
)

if TYPE_CHECKING:
    from dipeo_domain import models as domain

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

  // Handle Map types (ES6 Map)
  if (tsType.startsWith('Map<')) {
    // Extract content between < and >
    const mapContent = tsType.slice(4, -1);
    
    // Find comma separating key and value types, handling nested generics
    let depth = 0;
    let commaIndex = -1;
    for (let i = 0; i < mapContent.length; i++) {
      if (mapContent[i] === '<') depth++;
      else if (mapContent[i] === '>') depth--;
      else if (mapContent[i] === ',' && depth === 0) {
        commaIndex = i;
        break;
      }
    }
    
    if (commaIndex !== -1) {
      const keyType = mapContent.slice(0, commaIndex).trim();
      const valueType = mapContent.slice(commaIndex + 1).trim();
      
      // Remove import() statements and extract the type name
      const cleanKeyType = keyType.replace(/import\([^)]+\)\./g, '');
      const cleanValueType = valueType.replace(/import\([^)]+\)\./g, '');
      
      return `Dict[${mapTypeToPython(cleanKeyType)}, ${mapTypeToPython(cleanValueType)}]`;
    }
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

// Determine if a type should have conversion methods
function shouldHaveConversion(typeDef: TypeDef): boolean {
  const conversionTypes = ['DomainNode', 'DomainDiagram', 'DomainPerson', 'ExecutionState', 'NodeState'];
  return conversionTypes.includes(typeDef.name);
}

// Generate field with validation
function generateFieldWithValidation(prop: Property, isOptional: boolean): string {
  const pythonName = prop.name;
  const pythonType = mapTypeToPython(prop.type);
  let fieldDef = '';
  
  // Add field constraints based on type
  const constraints: string[] = [];
  if (prop.description) {
    constraints.push(`description="${prop.description}"`);
  }
  
  // Add type-specific constraints
  if (pythonType === 'str' && prop.name.includes('id')) {
    constraints.push('min_length=1');
  } else if (pythonType === 'float' || pythonType === 'int') {
    if (prop.name.includes('count') || prop.name.includes('size')) {
      constraints.push('ge=0');
    }
  } else if (pythonType.startsWith('List[')) {
    constraints.push('min_items=0');
  }
  
  const fieldConstraints = constraints.length > 0 ? `Field(${constraints.join(', ')})` : null;
  
  if (isOptional) {
    if (fieldConstraints) {
      fieldDef = `    ${pythonName}: Optional[${pythonType}] = ${fieldConstraints}`;
    } else {
      fieldDef = `    ${pythonName}: Optional[${pythonType}] = None`;
    }
  } else {
    if (fieldConstraints) {
      fieldDef = `    ${pythonName}: ${pythonType} = ${fieldConstraints}`;
    } else {
      fieldDef = `    ${pythonName}: ${pythonType}`;
    }
  }
  
  return fieldDef;
}

// Types that are imported from domain and shouldn't be regenerated
const DOMAIN_TYPES = new Set([
  'NodeID', 'ArrowID', 'HandleID', 'PersonID', 'ApiKeyID', 'DiagramID', 'ExecutionID',
  'Message', 'MemoryConfig', 'MemoryState', 'Vec2', 'HandleDirection', 'NodeType', 'DataType', 
  'ForgettingMode', 'DiagramFormat', 'DBBlockSubType', 'ContentType', 'SupportedLanguage',
  'ExecutionStatus', 'NodeExecutionStatus', 'EventType', 'LLMService', 'NotionOperation'
]);

// Generate Python DTO from TypeDef
function generateDTO(typeDef: TypeDef, suffix: string = 'DTO'): string {
  // Skip types that are imported from domain
  if (DOMAIN_TYPES.has(typeDef.name)) {
    return '';
  }
  
  if (typeDef.type === 'enum') {
    let result = `class ${typeDef.name}${suffix}(str, Enum):\n`;
    typeDef.values?.forEach(value => {
      const pythonName = value.toUpperCase();
      result += `    ${pythonName} = "${value}"\n`;
    });
    return `${result  }\n`;
  }

  if (typeDef.type === 'type' && typeDef.value) {
    // Skip ID types that are imported from domain
    if (DOMAIN_TYPES.has(typeDef.name)) {
      return '';
    }
    // For branded types, create simple aliases
    if (typeDef.value === 'string') {
      return `${typeDef.name}${suffix} = str\n`;
    }
    return `${typeDef.name}${suffix} = ${mapTypeToPython(typeDef.value)}\n`;
  }

  // Determine base class
  let baseClass = 'BaseDTO';
  if (suffix === 'Request') {
    baseClass = 'RequestDTO';
  } else if (suffix === 'Response') {
    baseClass = 'BaseDTO';  // Use BaseDTO for specific response types
  } else if (shouldHaveConversion(typeDef)) {
    baseClass = `ConvertibleDTO["domain.${typeDef.name}"]`;
  }
  
  // Generate class definition
  let result = `class ${typeDef.name}${suffix}(${baseClass}):\n`;
  if (typeDef.properties && typeDef.properties.length > 0) {
    result += `    """${typeDef.name} data transfer object."""\n`;
  }
  
  if (!typeDef.properties || typeDef.properties.length === 0) {
    result += '    pass\n';
    return `${result  }\n`;
  }

  // First, add all required fields
  const requiredFields = typeDef.properties.filter(p => !p.optional);
  const optionalFields = typeDef.properties.filter(p => p.optional);

  requiredFields.forEach(prop => {
    result += generateFieldWithValidation(prop, false) + '\n';
  });

  // Then add optional fields with defaults
  optionalFields.forEach(prop => {
    result += generateFieldWithValidation(prop, true) + '\n';
  });
  
  // Add conversion methods if needed
  if (shouldHaveConversion(typeDef) && suffix === '') {
    result += `\n    @classmethod\n`;
    result += `    def from_domain(cls, domain_model: "domain.${typeDef.name}") -> "${typeDef.name}${suffix}":\n`;
    result += `        """Convert from domain model to DTO."""\n`;
    result += `        from dipeo_domain import models as domain\n`;
    result += `        return cls(\n`;
    
    typeDef.properties?.forEach((prop, idx) => {
      const pythonName = prop.name;
      const isLast = idx === typeDef.properties!.length - 1;
      result += `            ${pythonName}=domain_model.${pythonName}${isLast ? '' : ','}\n`;
    });
    
    result += `        )\n\n`;
    
    result += `    def to_domain(self) -> "domain.${typeDef.name}":\n`;
    result += `        """Convert from DTO to domain model."""\n`;
    result += `        from dipeo_domain import models as domain\n`;
    result += `        return domain.${typeDef.name}(\n`;
    
    typeDef.properties?.forEach((prop, idx) => {
      const pythonName = prop.name;
      const isLast = idx === typeDef.properties!.length - 1;
      result += `            ${pythonName}=self.${pythonName}${isLast ? '' : ','}\n`;
    });
    
    result += `        )\n`;
  }

  return `${result  }\n`;
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

  // Add utility functions
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