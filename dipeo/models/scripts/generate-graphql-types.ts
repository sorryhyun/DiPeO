#!/usr/bin/env tsx
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

interface FieldConfig {
  name: string;
  type: string;
  optional?: boolean;
  computed?: boolean;
  resolver?: string;
}

interface TypeConfig {
  domainType: string;
  graphqlType: string;
  fields?: string[];
  customFields?: FieldConfig[];
  allFields?: boolean;
}

interface SchemaDefinition {
  name: string;
  type: 'interface' | 'enum' | 'union' | 'alias';
  values?: string[];
}

class GraphQLTypesGenerator {
  private schema: Record<string, SchemaDefinition> = {};
  
  // Type mappings configuration
  private typeConfigs: TypeConfig[] = [
    // Simple types with all fields
    { domainType: 'Vec2', graphqlType: 'Vec2Type', allFields: true },
    { domainType: 'TokenUsage', graphqlType: 'TokenUsageType', allFields: true },
    { domainType: 'NodeState', graphqlType: 'NodeStateType', allFields: true },
    { domainType: 'DiagramMetadata', graphqlType: 'DiagramMetadataType', allFields: true },
    
    // Types with specific fields and custom resolvers
    {
      domainType: 'DomainHandle',
      graphqlType: 'DomainHandleType',
      fields: ['label', 'direction', 'data_type', 'position'],
      customFields: [
        { name: 'id', type: 'HandleID', resolver: 'HandleID(str(obj.id))' },
        { name: 'node_id', type: 'NodeID', resolver: 'NodeID(str(obj.node_id))' },
      ]
    },
    {
      domainType: 'DomainNode',
      graphqlType: 'DomainNodeType',
      fields: ['type', 'position'],
      customFields: [
        { name: 'id', type: 'NodeID', resolver: 'NodeID(str(obj.id))' },
        { name: 'data', type: 'JSONScalar', resolver: 'self._pydantic_object.data or {}' },
      ]
    },
    {
      domainType: 'DomainArrow',
      graphqlType: 'DomainArrowType',
      fields: ['content_type', 'label'],
      customFields: [
        { name: 'id', type: 'ArrowID', resolver: 'ArrowID(str(obj.id))' },
        { name: 'source', type: 'HandleID', resolver: 'HandleID(str(obj.source))' },
        { name: 'target', type: 'HandleID', resolver: 'HandleID(str(obj.target))' },
        { name: 'data', type: 'JSONScalar | None', resolver: 'self._pydantic_object.data', optional: true },
      ]
    },
    {
      domainType: 'PersonLLMConfig',
      graphqlType: 'PersonLLMConfigType',
      fields: ['service', 'model', 'system_prompt', 'voice', 'voice_id', 'audio_format'],
      customFields: [
        { 
          name: 'api_key_id', 
          type: 'ApiKeyID | None', 
          resolver: 'ApiKeyID(str(obj.api_key_id)) if obj and hasattr(obj, "api_key_id") and obj.api_key_id else None',
          optional: true 
        },
      ]
    },
    {
      domainType: 'DomainPerson',
      graphqlType: 'DomainPersonType',
      fields: ['label', 'llm_config'],
      customFields: [
        { name: 'id', type: 'PersonID', resolver: 'PersonID(str(obj.id))' },
        { name: 'type', type: 'str', resolver: '"person"' },
        { 
          name: 'masked_api_key', 
          type: 'str | None', 
          resolver: 'f"****{str(obj.llm_config.api_key_id)[-4:]}" if (obj and hasattr(obj, "llm_config") and obj.llm_config and obj.llm_config.api_key_id) else None',
          optional: true 
        },
      ]
    },
    {
      domainType: 'DomainApiKey',
      graphqlType: 'DomainApiKeyType',
      fields: ['label', 'service', 'key'],
      customFields: [
        { name: 'id', type: 'ApiKeyID', resolver: 'ApiKeyID(str(obj.id))' },
      ]
    },
    {
      domainType: 'DomainDiagram',
      graphqlType: 'DomainDiagramType',
      fields: ['nodes', 'handles', 'arrows', 'persons', 'metadata'],
      customFields: [
        { name: 'nodeCount', type: 'int', resolver: 'len(obj.nodes) if obj and hasattr(obj, "nodes") else 0', computed: true },
        { name: 'arrowCount', type: 'int', resolver: 'len(obj.arrows) if obj and hasattr(obj, "arrows") else 0', computed: true },
        { name: 'personCount', type: 'int', resolver: 'len(obj.persons) if obj and hasattr(obj, "persons") else 0', computed: true },
      ]
    },
    {
      domainType: 'ExecutionState',
      graphqlType: 'ExecutionStateType',
      fields: ['id', 'status', 'diagram_id', 'started_at', 'ended_at', 'token_usage', 'error', 'duration_seconds', 'is_active'],
      customFields: [
        { 
          name: 'node_states', 
          type: 'JSONScalar', 
          resolver: '{\n                node_id: state.model_dump() if hasattr(state, "model_dump") else state\n                for node_id, state in obj.node_states.items()\n            } if obj and hasattr(obj, "node_states") and obj.node_states else {}',
          computed: true 
        },
        { 
          name: 'node_outputs', 
          type: 'JSONScalar', 
          resolver: 'self._process_node_outputs(obj)',
          computed: true 
        },
        { 
          name: 'variables', 
          type: 'JSONScalar', 
          resolver: 'obj.variables if obj and hasattr(obj, "variables") else {}',
          computed: true 
        },
      ]
    },
  ];
  
  // Input types configuration
  private inputTypes = [
    {
      name: 'Vec2Input',
      fields: [
        { name: 'x', type: 'float' },
        { name: 'y', type: 'float' },
      ]
    },
    {
      name: 'CreateNodeInput',
      fields: [
        { name: 'type', type: 'NodeTypeEnum' },
        { name: 'position', type: 'Vec2Input' },
        { name: 'label', type: 'str' },
        { name: 'properties', type: 'JSONScalar | None', default: 'None' },
      ]
    },
    {
      name: 'UpdateNodeInput',
      fields: [
        { name: 'id', type: 'NodeID' },
        { name: 'position', type: 'Vec2Input | None', default: 'None' },
        { name: 'label', type: 'str | None', default: 'None' },
        { name: 'properties', type: 'JSONScalar | None', default: 'None' },
      ]
    },
    {
      name: 'CreateDiagramInput',
      fields: [
        { name: 'name', type: 'str' },
        { name: 'description', type: 'str | None', default: 'None' },
        { name: 'author', type: 'str | None', default: 'None' },
        { name: 'tags', type: 'list[str]', default: 'strawberry.field(default_factory=list)' },
      ]
    },
    {
      name: 'CreatePersonInput',
      fields: [
        { name: 'label', type: 'str' },
        { name: 'service', type: 'LLMServiceEnum' },
        { name: 'model', type: 'str' },
        { name: 'api_key_id', type: 'ApiKeyID' },
        { name: 'system_prompt', type: 'str | None', default: 'None' },
        { name: 'temperature', type: 'float | None', default: 'None' },
        { name: 'max_tokens', type: 'int | None', default: 'None' },
        { name: 'top_p', type: 'float | None', default: 'None' },
      ]
    },
    {
      name: 'UpdatePersonInput',
      fields: [
        { name: 'id', type: 'PersonID' },
        { name: 'label', type: 'str | None', default: 'None' },
        { name: 'model', type: 'str | None', default: 'None' },
        { name: 'api_key_id', type: 'ApiKeyID | None', default: 'None' },
        { name: 'system_prompt', type: 'str | None', default: 'None' },
        { name: 'temperature', type: 'float | None', default: 'None' },
        { name: 'max_tokens', type: 'int | None', default: 'None' },
        { name: 'top_p', type: 'float | None', default: 'None' },
      ]
    },
    {
      name: 'CreateApiKeyInput',
      fields: [
        { name: 'label', type: 'str' },
        { name: 'service', type: 'APIServiceTypeEnum' },
        { name: 'key', type: 'str' },
      ]
    },
    {
      name: 'ExecuteDiagramInput',
      fields: [
        { name: 'diagram_id', type: 'DiagramID | None', default: 'None' },
        { name: 'diagram_data', type: 'JSONScalar | None', default: 'None' },
        { name: 'variables', type: 'JSONScalar | None', default: 'None' },
        { name: 'debug_mode', type: 'bool', default: 'False' },
        { name: 'max_iterations', type: 'int', default: '100' },
        { name: 'timeout_seconds', type: 'int | None', default: 'None' },
      ]
    },
    {
      name: 'ExecutionControlInput',
      fields: [
        { name: 'execution_id', type: 'ExecutionID' },
        { name: 'action', type: 'str' },  // pause, resume, abort, skip_node
        { name: 'node_id', type: 'NodeID | None', default: 'None' },
      ]
    },
    {
      name: 'InteractiveResponseInput',
      fields: [
        { name: 'execution_id', type: 'ExecutionID' },
        { name: 'node_id', type: 'NodeID' },
        { name: 'response', type: 'str' },
      ]
    },
    {
      name: 'FileUploadInput',
      fields: [
        { name: 'filename', type: 'str' },
        { name: 'content_base64', type: 'str' },
        { name: 'content_type', type: 'str | None', default: 'None' },
      ]
    },
    {
      name: 'DiagramFilterInput',
      fields: [
        { name: 'name_contains', type: 'str | None', default: 'None' },
        { name: 'author', type: 'str | None', default: 'None' },
        { name: 'tags', type: 'list[str] | None', default: 'None' },
        { name: 'created_after', type: 'datetime | None', default: 'None' },
        { name: 'created_before', type: 'datetime | None', default: 'None' },
        { name: 'modified_after', type: 'datetime | None', default: 'None' },
      ]
    },
    {
      name: 'ExecutionFilterInput',
      fields: [
        { name: 'diagram_id', type: 'DiagramID | None', default: 'None' },
        { name: 'status', type: 'ExecutionStatusEnum | None', default: 'None' },
        { name: 'started_after', type: 'datetime | None', default: 'None' },
        { name: 'started_before', type: 'datetime | None', default: 'None' },
        { name: 'active_only', type: 'bool', default: 'False' },
      ]
    },
  ];
  
  // Result types configuration
  private resultTypes = [
    {
      name: 'MutationResult',
      base: null,
      fields: [
        { name: 'success', type: 'bool' },
        { name: 'message', type: 'str | None', default: 'None' },
        { name: 'error', type: 'str | None', default: 'None' },
      ]
    },
    {
      name: 'DiagramResult',
      base: 'MutationResult',
      fields: [
        { name: 'diagram', type: 'DomainDiagramType | None', default: 'None' },
      ]
    },
    {
      name: 'NodeResult',
      base: 'MutationResult',
      fields: [
        { name: 'node', type: 'DomainNodeType | None', default: 'None' },
      ]
    },
    {
      name: 'PersonResult',
      base: 'MutationResult',
      fields: [
        { name: 'person', type: 'DomainPersonType | None', default: 'None' },
      ]
    },
    {
      name: 'ApiKeyResult',
      base: 'MutationResult',
      fields: [
        { name: 'api_key', type: 'DomainApiKeyType | None', default: 'None' },
      ]
    },
    {
      name: 'TestApiKeyResult',
      base: 'MutationResult',
      fields: [
        { name: 'valid', type: 'bool | None', default: 'None' },
        { name: 'available_models', type: 'list[str] | None', default: 'None' },
      ]
    },
    {
      name: 'ExecutionResult',
      base: 'MutationResult',
      fields: [
        { name: 'execution', type: 'ExecutionStateType | None', default: 'None' },
        { name: 'execution_id', type: 'str | None', default: 'None' },
      ]
    },
    {
      name: 'DeleteResult',
      base: 'MutationResult',
      fields: [
        { name: 'deleted_count', type: 'int', default: '0' },
        { name: 'deleted_id', type: 'str | None', default: 'None' },
      ]
    },
    {
      name: 'FileUploadResult',
      base: 'MutationResult',
      fields: [
        { name: 'path', type: 'str | None', default: 'None' },
        { name: 'size_bytes', type: 'int | None', default: 'None' },
        { name: 'content_type', type: 'str | None', default: 'None' },
      ]
    },
    {
      name: 'DiagramFormatInfo',
      base: null,
      fields: [
        { name: 'id', type: 'str' },
        { name: 'name', type: 'str' },
        { name: 'description', type: 'str' },
        { name: 'extension', type: 'str' },
        { name: 'supports_import', type: 'bool' },
        { name: 'supports_export', type: 'bool' },
      ]
    },
  ];
  
  // Scalar types
  private scalarTypes = [
    { name: 'NodeID', description: 'Unique identifier for a node' },
    { name: 'DiagramID', description: 'Unique identifier for a diagram' },
    { name: 'ExecutionID', description: 'Unique identifier for an execution' },
    { name: 'PersonID', description: 'Unique identifier for a person' },
    { name: 'ApiKeyID', description: 'Unique identifier for an API key' },
    { name: 'HandleID', description: 'Unique identifier for a handle' },
    { name: 'ArrowID', description: 'Unique identifier for an arrow' },
  ];
  
  async generate() {
    console.log('Generating Python GraphQL types from TypeScript models...');
    
    // Load the generated schema
    const schemaPath = path.join(__dirname, '..', '__generated__', 'schemas.json');
    try {
      const schemaData = JSON.parse(fs.readFileSync(schemaPath, 'utf-8')) as SchemaDefinition[];
      // Convert array to object for easier lookup
      this.schema = schemaData.reduce((acc, def) => {
        acc[def.name] = def;
        return acc;
      }, {} as Record<string, SchemaDefinition>);
    } catch (error) {
      console.error('Failed to load schema. Make sure to run generate:schema first.');
      throw error;
    }
    
    const lines: string[] = [];
    
    // Header
    this.generateHeader(lines);
    
    // Imports
    this.generateImports(lines);
    
    // Scalar types
    this.generateScalarTypes(lines);
    
    // Enum conversions
    this.generateEnumConversions(lines);
    
    // Domain type conversions
    this.generateDomainTypes(lines);
    
    // Input types
    this.generateInputTypes(lines);
    
    // Result types
    this.generateResultTypes(lines);
    
    // Export all
    this.generateExports(lines);
    
    // Write file
    const outputPath = path.join(
      __dirname, '..', '..', '..',
      'apps', 'server', 'src', 'dipeo_server', 'api', 'graphql',
      'generated_types.py'
    );
    
    fs.writeFileSync(outputPath, lines.join('\n'));
    console.log(`Python GraphQL types generated at: ${outputPath}`);
  }
  
  private generateHeader(lines: string[]) {
    lines.push('"""');
    lines.push('THIS FILE WAS GENERATED - DO NOT EDIT');
    lines.push('Generated GraphQL types from TypeScript models');
    lines.push('Source: dipeo/models/scripts/generate-graphql-types.ts');
    lines.push('Run "make codegen" to regenerate');
    lines.push('"""');
  }
  
  private generateImports(lines: string[]) {
    lines.push('from datetime import datetime');
    lines.push('from typing import NewType');
    lines.push('');
    lines.push('import strawberry');
    lines.push('');
    
    // Import domain models - get all enums and types from schema
    const imports: string[] = [];
    for (const [name, def] of Object.entries(this.schema)) {
      if (def && (def.type === 'enum' || name.startsWith('Domain') || ['Vec2', 'TokenUsage', 'NodeState', 'ExecutionState', 'DiagramMetadata', 'PersonLLMConfig'].includes(name))) {
        imports.push(name);
      }
    }
    
    lines.push('from dipeo.models import (');
    imports.sort().forEach(imp => lines.push(`    ${imp},`));
    lines.push(')');
    lines.push('');
  }
  
  private generateScalarTypes(lines: string[]) {
    lines.push('# SCALAR TYPES');
    
    // Standard ID scalars
    for (const scalar of this.scalarTypes) {
      lines.push(`${scalar.name} = strawberry.scalar(`);
      lines.push(`    NewType("${scalar.name}", str),`);
      lines.push(`    description="${scalar.description}",`);
      lines.push(`    serialize=lambda v: str(v),`);
      lines.push(`    parse_value=lambda v: str(v) if v else None,`);
      lines.push(')');
      lines.push('');
    }
    
    // JSONScalar
    lines.push('JSONScalar = strawberry.scalar(');
    lines.push('    NewType("JSONScalar", object),');
    lines.push('    name="JSONScalar",');
    lines.push('    description="Arbitrary JSON data",');
    lines.push('    serialize=lambda v: v,');
    lines.push('    parse_value=lambda v: v,');
    lines.push(')');
    lines.push('');
  }
  
  private generateEnumConversions(lines: string[]) {
    lines.push('# ENUM CONVERSIONS');
    
    const enums: string[] = [];
    for (const [name, def] of Object.entries(this.schema)) {
      if (def && def.type === 'enum') {
        enums.push(name);
      }
    }
    
    enums.sort().forEach(enumName => {
      lines.push(`${enumName}Enum = strawberry.enum(${enumName})`);
    });
    lines.push('');
  }
  
  private generateDomainTypes(lines: string[]) {
    lines.push('# DOMAIN TYPE CONVERSIONS');
    lines.push('');
    
    for (const config of this.typeConfigs) {
      if (config.allFields) {
        // Simple type with all fields
        lines.push(`@strawberry.experimental.pydantic.type(${config.domainType}, all_fields=True)`);
        lines.push(`class ${config.graphqlType}:`);
        lines.push('    pass');
      } else {
        // Type with specific fields
        const fields = config.fields ? `fields=[${config.fields.map(f => `"${f}"`).join(', ')}]` : '';
        lines.push(`@strawberry.experimental.pydantic.type(`);
        lines.push(`    ${config.domainType},`);
        if (fields) {
          lines.push(`    ${fields}`);
        }
        lines.push(')');
        lines.push(`class ${config.graphqlType}:`);
        
        // Add custom fields
        if (config.customFields) {
          for (const field of config.customFields) {
            lines.push('    @strawberry.field');
            lines.push(`    def ${field.name}(self) -> ${field.type}:`);
            lines.push('        obj = self._pydantic_object if hasattr(self, "_pydantic_object") else self');
            if (field.resolver && field.resolver === 'self._process_node_outputs(obj)') {
              // Special case for node_outputs
              lines.push('        if obj and hasattr(obj, "node_outputs") and obj.node_outputs:');
              lines.push('            result = {}');
              lines.push('            for node_id, output in obj.node_outputs.items():');
              lines.push('                if output is None:');
              lines.push('                    result[node_id] = None');
              lines.push('                elif hasattr(output, "model_dump"):');
              lines.push('                    result[node_id] = output.model_dump()');
              lines.push('                else:');
              lines.push('                    result[node_id] = output');
              lines.push('            return result');
              lines.push('        return {}');
            } else if (field.resolver && field.resolver.includes('\n')) {
              // Multi-line resolver
              const resolverLines = field.resolver.split('\n');
              lines.push(`        return ${resolverLines[0]}`);
              resolverLines.slice(1).forEach(line => lines.push(`            ${line}`));
            } else {
              lines.push(`        return ${field.resolver}`);
            }
            lines.push('');
          }
        }
      }
      lines.push('');
    }
  }
  
  private generateInputTypes(lines: string[]) {
    lines.push('# INPUT TYPES');
    lines.push('');
    
    for (const inputType of this.inputTypes) {
      lines.push('@strawberry.input');
      lines.push(`class ${inputType.name}:`);
      
      for (const field of inputType.fields) {
        const defaultValue = field.default ? ` = ${field.default}` : '';
        lines.push(`    ${field.name}: ${field.type}${defaultValue}`);
      }
      
      lines.push('');
    }
  }
  
  private generateResultTypes(lines: string[]) {
    lines.push('# RESULT TYPES');
    lines.push('');
    
    for (const resultType of this.resultTypes) {
      lines.push('@strawberry.type');
      if (resultType.base) {
        lines.push(`class ${resultType.name}(${resultType.base}):`);
      } else {
        lines.push(`class ${resultType.name}:`);
      }
      
      for (const field of resultType.fields) {
        const defaultValue = field.default ? ` = ${field.default}` : '';
        lines.push(`    ${field.name}: ${field.type}${defaultValue}`);
      }
      
      lines.push('');
    }
  }
  
  private generateExports(lines: string[]) {
    lines.push('# Export all types');
    lines.push('__all__ = [');
    
    const exports: string[] = [];
    
    // Scalar types
    this.scalarTypes.forEach(s => exports.push(s.name));
    exports.push('JSONScalar');
    
    // Enum types
    for (const [name, def] of Object.entries(this.schema)) {
      if (def && def.type === 'enum') {
        exports.push(`${name}Enum`);
      }
    }
    
    // Domain types
    this.typeConfigs.forEach(c => exports.push(c.graphqlType));
    
    // Input types
    this.inputTypes.forEach(t => exports.push(t.name));
    
    // Result types
    this.resultTypes.forEach(t => exports.push(t.name));
    
    // Sort and output
    exports.sort().forEach(exp => lines.push(`    "${exp}",`));
    
    lines.push(']');
    lines.push('');
  }
}

// Run the generator
const generator = new GraphQLTypesGenerator();
generator.generate().catch(console.error);