import { parse, stringify } from 'yaml';
import { DiagramAssembler, Edge, NodeAnalysis, AssemblerCallbacks, ConverterDiagram } from './diagramAssembler';
import { buildNode, NodeInfo } from './nodeBuilders';
import { 
  generateShortId,
  entityIdGenerators,
  DomainDiagram,
  DomainPerson,
  DomainApiKey,
  DomainNode,
  NodeKind,
  nodeId,
  arrowId,
  personId,
  apiKeyId,
  NodeID,
  ArrowID,
  PersonID,
  ApiKeyID
} from '@/types';


interface LLMYamlFormat {
  flow: Record<string, string | string[]> | string[];
  prompts?: Record<string, string>;
  persons?: Record<string, string | {
    model?: string;
    service?: string;
    system?: string;
    temperature?: number;
  }>;
  data?: Record<string, string>;
}

export class LlmYaml {
  /**
   * Import LLM-friendly YAML and convert to DiagramState format
   */
  static fromLLMYAML(yamlString: string): ConverterDiagram {
    const data = parse(yamlString) as LLMYamlFormat;
    const assembler = new DiagramAssembler();
    
    const callbacks: AssemblerCallbacks = {
      parseFlow: (flowData) => LlmYaml.parseFlow(flowData),
      
      inferNodeType: (name, context) => LlmYaml.inferNodeType(name, context),
      
      createNodeInfo: (name, analysis, context) => {
        const nodeInfo: NodeInfo = {
          name,
          type: analysis.type as NodeKind,
          position: { x: 0, y: 0 }, // Will be set by assembler
          hasPrompt: !!context.prompts?.[name],
          hasPerson: !!context.persons?.[name],
          prompt: context.prompts?.[name],
          dataSource: context.data?.[name]
        };
        
        // Handle condition nodes
        if (analysis.type === 'condition') {
          const conditions = analysis.outgoing
            .map(e => e.condition)
            .filter(Boolean);
          nodeInfo.condition = conditions.length > 0 ? `${name}_check` : '';
        }
        
        // Build and return node
        const node = buildNode(nodeInfo);
        return {
          id: node.id,
          type: node.type,
          data: node.data
        };
      },
      
      createArrowData: (edge, sourceId, targetId) => ({
        id: `arrow-${generateShortId()}`,
        sourceBlockId: sourceId,
        targetBlockId: targetId,
        label: edge.variable || 'flow',
        contentType: edge.variable ? 'variable_in_object' : 'raw_text',
        branch: edge.condition ? 
          (edge.condition.includes('not') || edge.condition.startsWith('!') ? 'false' : 'true') 
          : undefined
      }),
      
      extractPersons: (nodeAnalysis, context) => LlmYaml.buildPersons(nodeAnalysis, context, assembler.getPersonMap()),
      
      extractApiKeys: (persons) => LlmYaml.extractApiKeys(persons),
      
      linkPersonsToNodes: (nodes: DomainNode[], nodeAnalysis, context) => {
        LlmYaml.linkPersonsToNodes(nodes, assembler.getNodeMap(), nodeAnalysis, context, assembler.getPersonMap());
      }
    };
    
    return assembler.assemble({ source: data, callbacks });
  }

  /**
   * Export DiagramState to LLM-friendly YAML format
   */
  static toLLMYAML(diagram: ConverterDiagram): string {
    const importer = new LlmYaml();
    return importer.exportYaml(diagram);
  }

  private static parseFlow(flowData: LLMYamlFormat['flow']): Edge[] {
    const edges: Edge[] = [];

    if (typeof flowData === 'object' && !Array.isArray(flowData)) {
      // Dictionary format: key -> value
      Object.entries(flowData).forEach(([source, targets]) => {
        if (typeof targets === 'string') {
          const edge = LlmYaml.parseEdge(source, targets);
          if (edge) edges.push(edge);
        } else if (Array.isArray(targets)) {
          targets.forEach(target => {
            const edge = LlmYaml.parseEdge(source, String(target));
            if (edge) edges.push(edge);
          });
        }
      });
    } else if (Array.isArray(flowData)) {
      // List format
      flowData.forEach(item => {
        const edge = LlmYaml.parseEdgeString(item);
        if (edge) edges.push(edge);
      });
    }

    return edges;
  }

  private static parseEdge(source: string, targetStr: string): Edge | null {
    // Pattern: target [condition]: "variable"
    const match = targetStr.trim().match(/(\w+)(?:\s*\[([^\]]+)\])?(?:\s*:\s*"([^"]+)")?/);
    if (match) {
      const [, target, condition, variable] = match;
      return {
        source: source.trim(),
        target: target?.trim() || '',
        condition: condition?.trim() || null,
        variable: variable?.trim() || null
      };
    }
    return null;
  }

  private static parseEdgeString(edgeStr: string): Edge | null {
    // Pattern: source -> target [condition]: "variable"
    const match = edgeStr.trim().match(/(\w+)\s*->\s*(\w+)(?:\s*\[([^\]]+)\])?(?:\s*:\s*"([^"]+)")?/);
    if (match) {
      const [, source, target, condition, variable] = match;
      return {
        source: source?.trim() || '',
        target: target?.trim() || '',
        condition: condition?.trim() || null,
        variable: variable?.trim() || null
      };
    }
    return null;
  }

  private static inferNodeType(name: string, data: LLMYamlFormat): string {
    const nameLower = name.toLowerCase();

    if (nameLower === 'start') return 'start';
    if (nameLower === 'end') return 'endpoint';
    if (data.prompts?.[name]) return 'person_job';
    if (nameLower.includes('condition') || nameLower.includes('check') || nameLower.includes('if')) {
      return 'condition';
    }
    if (nameLower.includes('data') || nameLower.includes('file') || nameLower.includes('load')) {
      return 'db';
    }
    return 'generic';
  }

  private static buildPersons(nodeAnalysis: Record<string, NodeAnalysis>, data: LLMYamlFormat, personMap: Map<string, PersonID>): DomainPerson[] {
    const persons: DomainPerson[] = [];
    const personsData = data.persons || {};
    const serviceMap = new Map<string, DomainApiKey['service']>();

    // Default person for nodes with prompts but no specific person
    const defaultPersonId = personId(`PERSON_${generateShortId()}`);
    const defaultPerson: DomainPerson = {
      id: defaultPersonId,
      label: 'Default Assistant',
      model: 'gpt-4.1-nano',
      service: 'openai',
    };
    let needDefault = false;

    // Create persons from persons section
    Object.entries(personsData).forEach(([personName, personConfig]) => {
      const personIdValue = personId(`PERSON_${generateShortId()}`);
      personMap.set(personName, personIdValue);

      if (typeof personConfig === 'string') {
        // Simple format: just system prompt
        persons.push({
          id: personIdValue,
          label: personName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          model: 'gpt-4.1-nano',
          service: 'openai',
          systemPrompt: personConfig
        });
        serviceMap.set(personIdValue, 'openai');
      } else {
        // Full format
        const service = (personConfig.service || 'openai') as DomainApiKey['service'];
        persons.push({
          id: personIdValue,
          label: personName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          model: personConfig.model || 'gpt-4.1-nano',
          service,
          systemPrompt: personConfig.system
        });
        serviceMap.set(personIdValue, service);
      }
    });

    // Check if we need default person
    const hasPromptNodes = Object.values(nodeAnalysis).some((analysis: NodeAnalysis) => {
      // Check if this node has prompts based on context
      return Object.keys(data.prompts || {}).includes(analysis.name);
    });
    if (hasPromptNodes && !persons.length) {
      needDefault = true;
    }

    // Check if any prompt nodes don't have matching persons
    Object.entries(nodeAnalysis).forEach(([name, _analysis]) => {
      if (data.prompts?.[name] && !personsData[name]) {
        needDefault = true;
      }
    });

    if (needDefault) {
      persons.push(defaultPerson);
      personMap.set('_default', defaultPersonId);
      serviceMap.set(defaultPersonId, 'openai');
    }

    // Store serviceMap for later use
    (LlmYaml as any)._serviceMap = serviceMap;

    return persons;
  }

  private static extractApiKeys(persons: DomainPerson[]): DomainApiKey[] {
    const apiKeys: Record<string, DomainApiKey> = {};
    const serviceMap = (LlmYaml as any)._serviceMap as Map<string, DomainApiKey['service']>;

    persons.forEach(person => {
      // Get service from our map
      const service = serviceMap?.get(person.id) || 'openai';
      if (!apiKeys[service]) {
        const apiKeyIdValue = apiKeyId(entityIdGenerators.apiKey());
        apiKeys[service] = {
          id: apiKeyIdValue,
          name: `${service.charAt(0).toUpperCase() + service.slice(1)} API Key`,
          service: service as DomainApiKey['service']
        };
      }
    });

    // Clean up
    delete (LlmYaml as any)._serviceMap;

    return Object.values(apiKeys);
  }

  private static linkPersonsToNodes(
    nodes: DomainNode[],
    nodeMap: Map<string, NodeID>, 
    nodeAnalysis: Record<string, NodeAnalysis>, 
    data: LLMYamlFormat, 
    personMap: Map<string, string>
  ): void {
    nodes.forEach(node => {
      // Find original name from nodeMap
      const originalName = Array.from(nodeMap.entries()).find(([, id]) => id === node.id)?.[0];
      if (!originalName) return;

      const analysis = nodeAnalysis[originalName];
      if (analysis && node.data.type === 'person_job') {
        const nodeData = node.data;
        
        // Check if this node has a specific person
        if (data.persons?.[originalName]) {
          nodeData.personId = personMap.get(originalName);
        } else if (data.prompts?.[originalName]) {
          // Use default person
          nodeData.personId = personMap.get('_default');
        }
      }
    });
  }


  /**
   * Export DiagramState to LLM-friendly YAML format
   */
  private exportYaml(diagram: ConverterDiagram): string {
    const flow: string[] = [];
    const prompts: Record<string, string> = {};
    const persons: Record<string, unknown> = {};
    const data: Record<string, unknown> = {};

    // Create reverse mapping from node ID to simple name
    const nodeNameMap: Record<string, string> = {};
    const personNameMap: Record<string, string> = {};

    // Map nodes to simple names
    diagram.nodes.forEach((node, index) => {
      let nodeName = '';
      if (node.type === 'start') {
        nodeName = 'START';
      } else if (node.type === 'endpoint') {
        nodeName = 'END';
      } else if (node.data.label) {
        nodeName = (node.data.label as string).replace(/\s+/g, '_').toLowerCase();
      } else {
        nodeName = `node_${index + 1}`;
      }

      // Ensure unique names
      let finalName = nodeName;
      let counter = 1;
      while (nodeNameMap[finalName]) {
        finalName = `${nodeName}_${counter}`;
        counter++;
      }
      nodeNameMap[node.id] = finalName;
    });

    // Map persons to names
    diagram.persons.forEach((person, index) => {
      const personName = person.label?.replace(/\s+/g, '_').toLowerCase() || `person_${index + 1}`;
      personNameMap[person.id] = personName;
    });

    // Build flow from arrows
    const flowMap: Record<string, string[]> = {};
    diagram.arrows.forEach(arrow => {
      const sourceName = nodeNameMap[arrow.source];
      const targetName = nodeNameMap[arrow.target];
      if (!sourceName || !targetName) return;

      let targetStr = targetName;

      // Add condition if this is a branch
      if (arrow.data?.branch) {
        const condition = arrow.data.branch === 'true' ? 'if' : 'if not';
        targetStr = `${targetName} [${condition}]`;
      }

      // Add variable if present
      if (arrow.data?.label && arrow.data.label !== 'flow') {
        targetStr += `: "${arrow.data.label}"`;
      }

      if (!flowMap[sourceName]) {
        flowMap[sourceName] = [];
      }
      flowMap[sourceName].push(targetStr);
    });

    // Convert flow map to array format
    Object.entries(flowMap).forEach(([source, targets]) => {
      if (targets.length === 1) {
        flow.push(`${source} -> ${targets[0]}`);
      } else {
        targets.forEach(target => {
          flow.push(`${source} -> ${target}`);
        });
      }
    });

    // Extract prompts and data from nodes
    diagram.nodes.forEach(node => {
      const nodeName = nodeNameMap[node.id];
      
      if (nodeName && node.type === 'person_job' && node.data.type === 'person_job') {
        if (node.data.defaultPrompt) {
          prompts[nodeName] = String(node.data.defaultPrompt);
        }
      } else if (nodeName && node.type === 'db' && node.data.type === 'db') {
        if (node.data.sourceDetails) {
          data[nodeName] = node.data.sourceDetails;
        }
      }
    });

    // Extract persons from diagram persons
    diagram.persons.forEach(person => {
      const personName = personNameMap[person.id];
      
      // Use service from person
      const service = person.service || 'openai'; // default
      
      if (personName && (person.systemPrompt || person.model !== 'gpt-4' || service !== 'openai')) {
        const personData: Record<string, unknown> = {};
        
        if (person.model && person.model !== 'gpt-4') {
          personData.model = person.model;
        }
        if (service && service !== 'openai') {
          personData.service = service;
        }
        if (person.systemPrompt) {
          personData.system = person.systemPrompt;
        }

        // Simplify if only system prompt
        if (Object.keys(personData).length === 1 && personData.system) {
          persons[personName] = personData.system as string;
        } else {
          persons[personName] = personData;
        }
      }
    });

    // Build final YAML structure
    const yamlData: Record<string, unknown> = {
      flow
    };

    if (Object.keys(prompts).length > 0) {
      yamlData.prompts = prompts;
    }

    if (Object.keys(persons).length > 0) {
      yamlData.persons = persons;
    }

    if (Object.keys(data).length > 0) {
      yamlData.data = data;
    }

    return stringify(yamlData, {
      indent: 2,
      lineWidth: 120,
      defaultKeyType: 'PLAIN',
      defaultStringType: 'QUOTE_DOUBLE'
    });
  }
}