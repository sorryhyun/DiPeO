#!/usr/bin/env tsx
import fs from 'fs/promises';
import path from 'path';
import process from 'node:process';
import { fileURLToPath } from 'url';
import { SchemaDefinition } from './generate-schema';
import { loadSchemas } from './load-schema';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Mapping from TypeScript node data interfaces to Python static node classes
const NODE_DATA_TO_STATIC_MAP: Record<string, { nodeType: string; fields: Array<{ tsName: string; pyName: string; defaultValue?: string }> }> = {
  StartNodeData: {
    nodeType: 'start',
    fields: [
      { tsName: 'custom_data', pyName: 'custom_data', defaultValue: 'field(default_factory=dict)' },
      { tsName: 'output_data_structure', pyName: 'output_data_structure', defaultValue: 'field(default_factory=dict)' },
      { tsName: 'trigger_mode', pyName: 'trigger_mode' },
      { tsName: 'hook_event', pyName: 'hook_event' },
      { tsName: 'hook_filters', pyName: 'hook_filters' }
    ]
  },
  EndpointNodeData: {
    nodeType: 'endpoint',
    fields: [
      { tsName: 'save_to_file', pyName: 'save_to_file', defaultValue: 'False' },
      { tsName: 'file_name', pyName: 'file_name' }
    ]
  },
  PersonJobNodeData: {
    nodeType: 'person_job',
    fields: [
      { tsName: 'person', pyName: 'person_id' },
      { tsName: 'first_only_prompt', pyName: 'first_only_prompt', defaultValue: '""' },
      { tsName: 'default_prompt', pyName: 'default_prompt' },
      { tsName: 'max_iteration', pyName: 'max_iteration', defaultValue: '1' },
      { tsName: 'memory_config', pyName: 'memory_config' },
      { tsName: 'tools', pyName: 'tools' }
    ]
  },
  ConditionNodeData: {
    nodeType: 'condition',
    fields: [
      { tsName: 'condition_type', pyName: 'condition_type', defaultValue: '""' },
      { tsName: 'expression', pyName: 'expression' },
      { tsName: 'node_indices', pyName: 'node_indices' }
    ]
  },
  CodeJobNodeData: {
    nodeType: 'code_job',
    fields: [
      { tsName: 'language', pyName: 'language', defaultValue: 'SupportedLanguage.python' },
      { tsName: 'code', pyName: 'code', defaultValue: '""' },
      { tsName: 'timeout', pyName: 'timeout' }
    ]
  },
  ApiJobNodeData: {
    nodeType: 'api_job',
    fields: [
      { tsName: 'url', pyName: 'url', defaultValue: '""' },
      { tsName: 'method', pyName: 'method', defaultValue: 'HttpMethod.GET' },
      { tsName: 'headers', pyName: 'headers' },
      { tsName: 'params', pyName: 'params' },
      { tsName: 'body', pyName: 'body' },
      { tsName: 'timeout', pyName: 'timeout' },
      { tsName: 'auth_type', pyName: 'auth_type' },
      { tsName: 'auth_config', pyName: 'auth_config' }
    ]
  },
  DBNodeData: {
    nodeType: 'db',
    fields: [
      { tsName: 'file', pyName: 'file' },
      { tsName: 'collection', pyName: 'collection' },
      { tsName: 'sub_type', pyName: 'sub_type', defaultValue: 'DBBlockSubType.fixed_prompt' },
      { tsName: 'operation', pyName: 'operation', defaultValue: '""' },
      { tsName: 'query', pyName: 'query' },
      { tsName: 'data', pyName: 'data' }
    ]
  },
  UserResponseNodeData: {
    nodeType: 'user_response',
    fields: [
      { tsName: 'prompt', pyName: 'prompt', defaultValue: '""' },
      { tsName: 'timeout', pyName: 'timeout', defaultValue: '60' }
    ]
  },
  NotionNodeData: {
    nodeType: 'notion',
    fields: [
      { tsName: 'operation', pyName: 'operation', defaultValue: 'NotionOperation.read_page' },
      { tsName: 'page_id', pyName: 'page_id' },
      { tsName: 'database_id', pyName: 'database_id' }
    ]
  },
  HookNodeData: {
    nodeType: 'hook',
    fields: [
      { tsName: 'hook_type', pyName: 'hook_type', defaultValue: 'HookType.shell' },
      { tsName: 'config', pyName: 'config', defaultValue: 'field(default_factory=dict)' },
      { tsName: 'timeout', pyName: 'timeout' },
      { tsName: 'retry_count', pyName: 'retry_count' },
      { tsName: 'retry_delay', pyName: 'retry_delay' }
    ]
  }
};

// Type mappings
const TS_TO_PY_TYPE: Record<string, string> = {
  'string': 'str',
  'number': 'int',
  'boolean': 'bool',
  'PersonID': 'Optional[PersonID]',
  'MemoryConfig': 'Optional[MemoryConfig]',
  'ToolConfig[]': 'Optional[List[ToolConfig]]',
  'string[]': 'Optional[List[str]]',
  'Record<string, any>': 'Dict[str, Any]',
  'Record<string, string>': 'Dict[str, str]',
  'Record<string, string | number | boolean>': 'Dict[str, Union[str, int, bool]]',
  'any': 'Any',
  'HookTriggerMode': 'Optional[HookTriggerMode]',
  'SupportedLanguage': 'SupportedLanguage',
  'HttpMethod': 'HttpMethod',
  'DBBlockSubType': 'DBBlockSubType',
  'NotionOperation': 'NotionOperation',
  'HookType': 'HookType'
};

class StaticNodeGenerator {
  private schemas = new Map<string, SchemaDefinition>();

  constructor(private all: SchemaDefinition[]) {
    all.forEach(s => this.schemas.set(s.name, s));
  }

  private getPythonType(tsType: string | undefined, optional: boolean): string {
    if (!tsType) return 'Any';
    
    // Clean up the type string
    tsType = tsType.trim()
      .replace(/\s*\|\s*null/g, '')
      .replace(/\s*\|\s*undefined/g, '')
      .replace(/^import\([^)]+\)\./, ''); // Remove import() wrapper
    
    // Handle string literal unions like 'none' | 'bearer' | 'basic' | 'api_key'
    if ((tsType.includes('"') || tsType.includes("'")) && tsType.includes('|')) {
      // Extract the individual string literals and quote them properly for Python
      const literals = tsType.split('|').map(lit => {
        const cleaned = lit.trim().replace(/['"]/g, '');
        return `"${cleaned}"`;
      });
      const literalType = `Literal[${literals.join(', ')}]`;
      return optional ? `Optional[${literalType}]` : literalType;
    }
    
    // Direct mapping
    if (TS_TO_PY_TYPE[tsType]) {
      return TS_TO_PY_TYPE[tsType];
    }
    
    // Handle arrays
    if (tsType.endsWith('[]')) {
      const innerType = tsType.slice(0, -2);
      return optional ? `Optional[List[${this.getPythonType(innerType, false)}]]` : `List[${this.getPythonType(innerType, false)}]`;
    }
    
    // Handle Record types
    if (tsType.startsWith('Record<')) {
      const match = tsType.match(/Record<([^,]+),\s*(.+)>/);
      if (match) {
        const keyType = match[1] === 'string' ? 'str' : match[1];
        const valueType = this.getPythonType(match[2], false);
        const dictType = `Dict[${keyType}, ${valueType}]`;
        return optional ? `Optional[${dictType}]` : dictType;
      }
    }
    
    // Handle optional types
    if (optional && !tsType.startsWith('Optional[')) {
      return `Optional[${this.getPythonType(tsType, false)}]`;
    }
    
    // Fallback for known types
    const knownTypes = ['HookTriggerMode', 'SupportedLanguage', 'HttpMethod', 'DBBlockSubType', 'NotionOperation', 'HookType'];
    if (knownTypes.includes(tsType)) {
      return optional ? `Optional[${tsType}]` : tsType;
    }
    
    return tsType;
  }

  private generateNodeClass(nodeName: string, schema: SchemaDefinition | undefined, mapping: typeof NODE_DATA_TO_STATIC_MAP[string]): string[] {
    const lines: string[] = [];
    const className = nodeName.replace('NodeData', 'Node');
    
    lines.push(`@dataclass(frozen=True)`);
    lines.push(`class ${className}(BaseExecutableNode):`);
    lines.push(`    type: NodeType = field(default=NodeType.${mapping.nodeType}, init=False)`);
    
    // Add fields
    if (schema?.properties) {
      for (const field of mapping.fields) {
        const prop = schema.properties[field.tsName];
        if (!prop) continue;
        
        // For HookNode config field, handle specially
        if (field.pyName === 'config' && nodeName === 'HookNodeData') {
          lines.push('    config: Dict[str, Any] = field(default_factory=dict)');
          continue;
        }
        
        const pyType = this.getPythonType(prop.type, prop.optional || false);
        let fieldDef = `    ${field.pyName}: ${pyType}`;
        
        if (field.defaultValue) {
          if (field.defaultValue.includes('field(')) {
            fieldDef += ` = ${field.defaultValue}`;
          } else {
            fieldDef += ` = ${field.defaultValue}`;
          }
        } else if (prop.optional || pyType.includes('Optional[')) {
          fieldDef += ' = None';
        } else if (!prop.optional && pyType.includes('Dict[') && !pyType.includes('Optional[')) {
          fieldDef += ' = field(default_factory=dict)';
        } else if (!prop.optional && pyType.includes('List[') && !pyType.includes('Optional[')) {
          fieldDef += ' = field(default_factory=list)';
        }
        
        lines.push(fieldDef);
      }
    }
    
    // Add to_dict method for node-specific fields
    lines.push('');
    lines.push('    def to_dict(self) -> Dict[str, Any]:');
    lines.push('        """Convert node to dictionary representation."""');
    lines.push('        data = super().to_dict()');
    
    // Add node-specific fields to the dict
    if (schema?.properties) {
      for (const field of mapping.fields) {
        const prop = schema.properties[field.tsName];
        if (!prop) continue;
        
        lines.push(`        data["${field.tsName}"] = self.${field.pyName}`);
      }
    }
    
    lines.push('        return data');
    lines.push('');
    return lines;
  }

  private generateFactoryFunction(): string[] {
    const lines: string[] = [];
    
    lines.push('def create_executable_node(');
    lines.push('    node_type: NodeType,');
    lines.push('    node_id: NodeID,');
    lines.push('    position: Vec2,');
    lines.push('    label: str = "",');
    lines.push('    data: Optional[Dict[str, Any]] = None,');
    lines.push('    flipped: bool = False,');
    lines.push('    metadata: Optional[Dict[str, Any]] = None');
    lines.push(') -> ExecutableNode:');
    lines.push('    """Factory function to create typed executable nodes from diagram data."""');
    lines.push('    data = data or {}');
    lines.push('    ');
    
    // Generate mapping for each node type
    for (const [dataInterface, mapping] of Object.entries(NODE_DATA_TO_STATIC_MAP)) {
      const className = dataInterface.replace('NodeData', 'Node');
      const nodeTypeEnum = `NodeType.${mapping.nodeType}`;
      
      lines.push(`    if node_type == ${nodeTypeEnum}:`);
      lines.push(`        return ${className}(`);
      lines.push('            id=node_id,');
      lines.push('            position=position,');
      lines.push('            label=label,');
      lines.push('            flipped=flipped,');
      lines.push('            metadata=metadata,');
      
      // Map fields
      for (const field of mapping.fields) {
        if (field.pyName === 'person_id' && field.tsName === 'person') {
          lines.push(`            ${field.pyName}=data.get("${field.tsName}"),`);
        } else if (field.pyName === 'config' && dataInterface === 'HookNodeData') {
          lines.push(`            config=data.get("config", {}),`);
        } else if (field.pyName === 'memory_config') {
          // Convert dict to MemoryConfig object
          lines.push(`            ${field.pyName}=MemoryConfig(**data.get("${field.tsName}")) if data.get("${field.tsName}") else None,`);
        } else if (field.defaultValue && !field.defaultValue.includes('field(')) {
          // For fields with default values (excluding field() defaults), use the default when None
          lines.push(`            ${field.pyName}=data.get("${field.tsName}", ${field.defaultValue}),`);
        } else {
          lines.push(`            ${field.pyName}=data.get("${field.tsName}"),`);
        }
      }
      
      lines.push('        )');
      lines.push('    ');
    }
    
    // Add PersonBatchJobNode special case
    lines.push('    if node_type == NodeType.person_batch_job:');
    lines.push('        return PersonBatchJobNode(');
    lines.push('            id=node_id,');
    lines.push('            position=position,');
    lines.push('            label=label,');
    lines.push('            flipped=flipped,');
    lines.push('            metadata=metadata,');
    lines.push('            person_id=data.get("person"),');
    lines.push('            first_only_prompt=data.get("first_only_prompt", ""),');
    lines.push('            default_prompt=data.get("default_prompt"),');
    lines.push('            max_iteration=data.get("max_iteration", 1),');
    lines.push('            memory_config=MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None,');
    lines.push('            tools=data.get("tools")');
    lines.push('        )');
    lines.push('    ');
    
    // Fallback
    lines.push('    raise ValueError(f"Unknown node type: {node_type}")');
    lines.push('');
    
    return lines;
  }

  async generate(dest: string) {
    const lines: string[] = [];
    
    // Header
    lines.push('"""');
    lines.push('Auto-generated static node types from domain models.');
    lines.push('DO NOT EDIT THIS FILE DIRECTLY.');
    lines.push('Generated by: dipeo/models/scripts/generate-static-nodes.ts');
    lines.push('"""');
    lines.push('');
    lines.push('from dataclasses import dataclass, field');
    lines.push('from typing import Dict, Any, Optional, List, Union, Literal');
    lines.push('');
    lines.push('from dipeo.models.models import (');
    lines.push('    NodeType, Vec2, NodeID, PersonID, MemoryConfig, ToolConfig,');
    lines.push('    HookTriggerMode, SupportedLanguage, HttpMethod, DBBlockSubType,');
    lines.push('    NotionOperation, HookType, PersonLLMConfig, LLMService');
    lines.push(')');
    lines.push('');
    lines.push('');
    
    // Base class
    lines.push('@dataclass(frozen=True)');
    lines.push('class BaseExecutableNode:');
    lines.push('    """Base class for all executable node types."""');
    lines.push('    id: NodeID');
    lines.push('    type: NodeType');
    lines.push('    position: Vec2');
    lines.push('    label: str = ""');
    lines.push('    flipped: bool = False');
    lines.push('    metadata: Optional[Dict[str, Any]] = None');
    lines.push('    ');
    lines.push('    def to_dict(self) -> Dict[str, Any]:');
    lines.push('        """Convert node to dictionary representation."""');
    lines.push('        result = {');
    lines.push('            "id": self.id,');
    lines.push('            "type": self.type.value,');
    lines.push('            "position": {"x": self.position.x, "y": self.position.y},');
    lines.push('            "label": self.label,');
    lines.push('            "flipped": self.flipped');
    lines.push('        }');
    lines.push('        if self.metadata:');
    lines.push('            result["metadata"] = self.metadata');
    lines.push('        return result');
    lines.push('');
    lines.push('');
    
    // Generate node classes
    for (const [dataInterface, mapping] of Object.entries(NODE_DATA_TO_STATIC_MAP)) {
      const schema = this.schemas.get(dataInterface);
      lines.push(...this.generateNodeClass(dataInterface, schema, mapping));
    }
    
    // PersonBatchJobNode (alias)
    lines.push('@dataclass(frozen=True)');
    lines.push('class PersonBatchJobNode(PersonJobNode):');
    lines.push('    """Person batch job node - same as PersonJobNode but with different type."""');
    lines.push('    type: NodeType = field(default=NodeType.person_batch_job, init=False)');
    lines.push('');
    lines.push('');
    
    // Union type
    lines.push('ExecutableNode = Union[');
    lines.push('    StartNode,');
    lines.push('    EndpointNode,');
    lines.push('    PersonJobNode,');
    lines.push('    ConditionNode,');
    lines.push('    CodeJobNode,');
    lines.push('    ApiJobNode,');
    lines.push('    DBNode,');
    lines.push('    UserResponseNode,');
    lines.push('    NotionNode,');
    lines.push('    PersonBatchJobNode,');
    lines.push('    HookNode');
    lines.push(']');
    lines.push('');
    lines.push('');
    
    // Factory function
    lines.push(...this.generateFactoryFunction());
    
    await fs.mkdir(path.dirname(dest), { recursive: true });
    await fs.writeFile(dest, lines.join('\n'));
  }
}

// CLI
if (import.meta.url === `file://${process.argv[1]}`) {
  (async () => {
    const schemas = await loadSchemas(path.resolve(__dirname, '../__generated__'));
    const out = path.resolve(__dirname, '../../core/static/generated_nodes.py');
    await new StaticNodeGenerator(schemas).generate(out);
    console.log(`Generated static nodes → ${out}`);
  })();
}