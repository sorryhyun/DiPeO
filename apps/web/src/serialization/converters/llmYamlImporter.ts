import { parse, stringify } from 'yaml';
import { nanoid } from 'nanoid';
import {
  DiagramState,
  DiagramNode,
  Arrow,
  PersonDefinition,
  ApiKey,
  PersonJobBlockData,
  ConditionBlockData,
  DBBlockData,
  StartBlockData,
  EndpointBlockData
} from '@/shared/types';

interface Edge {
  source: string;
  target: string;
  condition: string | null;
  variable: string | null;
}

interface NodeInfo {
  name: string;
  type: string;
  hasPrompt: boolean;
  hasAgent: boolean;
  incoming: Edge[];
  outgoing: Edge[];
}

interface LLMYamlFormat {
  flow: Record<string, string | string[]> | string[];
  prompts?: Record<string, string>;
  agents?: Record<string, string | {
    model?: string;
    service?: string;
    system?: string;
    temperature?: number;
  }>;
  data?: Record<string, string>;
}

export class LLMYamlImporter {
  private nodeMap: Record<string, string> = {};
  private personMap: Record<string, string> = {};

  /**
   * Import LLM-friendly YAML and convert to DiagramState format
   */
  static fromLLMYAML(yamlString: string): DiagramState {
    const importer = new LLMYamlImporter();
    return importer.importYaml(yamlString);
  }

  /**
   * Export DiagramState to LLM-friendly YAML format
   */
  static toLLMYAML(diagram: DiagramState): string {
    const importer = new LLMYamlImporter();
    return importer.exportYaml(diagram);
  }

  private importYaml(yamlContent: string): DiagramState {
    try {
      const data = parse(yamlContent) as LLMYamlFormat;

      // Parse flow to build graph structure
      const flowEdges = this.parseFlow(data.flow || {});

      // Extract node names and types
      const nodeInfo = this.analyzeNodes(flowEdges, data);

      // Build diagram components
      const nodes = this.buildNodes(nodeInfo, data);
      const arrows = this.buildArrows(flowEdges);
      const persons = this.buildPersons(nodeInfo, data);
      const apiKeys = this.extractApiKeys(persons);

      // Update nodes with person IDs
      this.linkPersonsToNodes(nodes, nodeInfo, data);

      return {
        nodes,
        arrows,
        persons,
        apiKeys
      };
    } catch (error) {
      // Return minimal valid diagram on error
      console.error('LLM YAML import error:', error);
      return {
        nodes: [{
          id: 'error-node',
          type: 'start',
          position: { x: 0, y: 0 },
          data: {
            id: 'error-node',
            label: `Import Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
            type: 'start'
          } as StartBlockData
        }],
        arrows: [],
        persons: [],
        apiKeys: []
      };
    }
  }

  private parseFlow(flowData: LLMYamlFormat['flow']): Edge[] {
    const edges: Edge[] = [];

    if (typeof flowData === 'object' && !Array.isArray(flowData)) {
      // Dictionary format: key -> value
      Object.entries(flowData).forEach(([source, targets]) => {
        if (typeof targets === 'string') {
          const edge = this.parseEdge(source, targets);
          if (edge) edges.push(edge);
        } else if (Array.isArray(targets)) {
          targets.forEach(target => {
            const edge = this.parseEdge(source, String(target));
            if (edge) edges.push(edge);
          });
        }
      });
    } else if (Array.isArray(flowData)) {
      // List format
      flowData.forEach(item => {
        if (typeof item === 'string') {
          const edge = this.parseEdgeString(item);
          if (edge) edges.push(edge);
        }
      });
    }

    return edges;
  }

  private parseEdge(source: string, targetStr: string): Edge | null {
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

  private parseEdgeString(edgeStr: string): Edge | null {
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

  private analyzeNodes(edges: Edge[], data: LLMYamlFormat): Record<string, NodeInfo> {
    const nodeInfo: Record<string, NodeInfo> = {};

    // Collect all nodes
    edges.forEach(edge => {
      [edge.source, edge.target].forEach(node => {
        if (!nodeInfo[node]) {
          nodeInfo[node] = {
            name: node,
            type: this.inferNodeType(node, data),
            hasPrompt: !!data.prompts?.[node],
            hasAgent: !!data.agents?.[node],
            incoming: [],
            outgoing: []
          };
        }
      });

      // Track connections
      nodeInfo[edge.source]?.outgoing.push(edge);
      nodeInfo[edge.target]?.incoming.push(edge);
    });

    // Refine node types based on connections
    Object.entries(nodeInfo).forEach(([_name, info]) => {
      // Nodes with conditions become condition nodes
      if (info.outgoing.some(e => e.condition)) {
        info.type = 'condition';
      }
      // Nodes with prompts become person jobs (unless already typed)
      else if (info.hasPrompt && info.type === 'generic') {
        info.type = 'person_job';
      }
    });

    return nodeInfo;
  }

  private inferNodeType(name: string, data: LLMYamlFormat): string {
    const nameLower = name.toLowerCase();

    if (nameLower === 'start') return 'start';
    if (nameLower === 'end') return 'endpoint';
    if (data.prompts?.[name]) return 'personjob';
    if (nameLower.includes('condition') || nameLower.includes('check') || nameLower.includes('if')) {
      return 'condition';
    }
    if (nameLower.includes('data') || nameLower.includes('file') || nameLower.includes('load')) {
      return 'db';
    }
    return 'generic';
  }

  private buildNodes(nodeInfo: Record<string, NodeInfo>, data: LLMYamlFormat): DiagramNode[] {
    const nodes: DiagramNode[] = [];
    const positions = this.calculatePositions(nodeInfo);

    Object.entries(nodeInfo).forEach(([name, info]) => {
      const nodeId = `${this.nodeTypeToId(info.type)}-${nanoid(6)}`;
      this.nodeMap[name] = nodeId;

      const baseData = {
        id: nodeId,
        label: name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      };

      let nodeData: any = baseData;

      switch (info.type) {
        case 'start':
          nodeData = {
            ...baseData,
            type: 'start'
          } as StartBlockData;
          break;

        case 'person_job':
          nodeData = {
            ...baseData,
            type: 'person_job',
            defaultPrompt: data.prompts?.[name] || '',
            firstOnlyPrompt: '',
            contextCleaningRule: 'uponRequest',
            iterationCount: 1,
            mode: 'sync',
            detectedVariables: this.detectVariables(data.prompts?.[name] || '')
          } as PersonJobBlockData;
          break;

        case 'condition': {
          // Extract condition expression
          const conditions = info.outgoing
            .map(e => e.condition)
            .filter(Boolean);
          
          nodeData = {
            ...baseData,
            type: 'condition',
            conditionType: 'expression',
            expression: conditions.length > 0 ? `${name}_check` : ''
          } as ConditionBlockData;
          break;
        }

        case 'db': {
          const dataSource = data.data?.[name];
          nodeData = {
            ...baseData,
            type: 'db',
            subType: dataSource && dataSource.match(/\.(txt|json|csv)$/) ? 'file' : 'fixed_prompt',
            sourceDetails: dataSource || ''
          } as DBBlockData;
          break;
        }

        case 'endpoint':
          nodeData = {
            ...baseData,
            type: 'endpoint',
            saveToFile: false,
            filePath: '',
            fileFormat: 'text'
          } as EndpointBlockData;
          break;

        default:
          // Default to personjob
          nodeData = {
            ...baseData,
            type: 'person_job',
            defaultPrompt: '',
            firstOnlyPrompt: '',
            contextCleaningRule: 'uponRequest',
            iterationCount: 1,
            mode: 'sync',
            detectedVariables: []
          } as PersonJobBlockData;
      }

      nodes.push({
        id: nodeId,
        type: this.nodeTypeToId(info.type),
        position: positions[name] || { x: 0, y: 0 },
        data: nodeData
      });
    });

    return nodes;
  }

  private buildArrows(edges: Edge[]): Arrow[] {
    const arrows: Arrow[] = [];

    edges.forEach(edge => {
      const sourceId = this.nodeMap[edge.source];
      const targetId = this.nodeMap[edge.target];

      if (!sourceId || !targetId) return;

      const arrowId = `arrow-${nanoid(6)}`;
      arrows.push({
        id: arrowId,
        source: sourceId,
        target: targetId,
        type: 'customArrow',
        data: {
          id: arrowId,
          sourceBlockId: sourceId,
          targetBlockId: targetId,
          label: edge.variable || 'flow',
          contentType: edge.variable ? 'variable_in_object' : 'raw_text',
          branch: edge.condition ? 
            (edge.condition.includes('not') || edge.condition.startsWith('!') ? 'false' : 'true') 
            : undefined
        }
      });
    });

    return arrows;
  }

  private buildPersons(nodeInfo: Record<string, NodeInfo>, data: LLMYamlFormat): PersonDefinition[] {
    const persons: PersonDefinition[] = [];
    const agentsData = data.agents || {};

    // Default agent for nodes with prompts but no specific agent
    const defaultPersonId = `PERSON_${nanoid(6)}`;
    const defaultPerson: PersonDefinition = {
      id: defaultPersonId,
      label: 'Default Assistant',
      modelName: 'gpt-4',
      service: 'openai'
    };
    let needDefault = false;

    // Create persons from agents section
    Object.entries(agentsData).forEach(([agentName, agentConfig]) => {
      const personId = `PERSON_${nanoid(6)}`;
      this.personMap[agentName] = personId;

      if (typeof agentConfig === 'string') {
        // Simple format: just system prompt
        persons.push({
          id: personId,
          label: agentName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          modelName: 'gpt-4',
          service: 'openai',
          systemPrompt: agentConfig
        });
      } else {
        // Full format
        persons.push({
          id: personId,
          label: agentName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          modelName: agentConfig.model || 'gpt-4',
          service: (agentConfig.service || 'openai') as any,
          systemPrompt: agentConfig.system
        });
      }
    });

    // Check if we need default person
    const hasPromptNodes = Object.values(nodeInfo).some(info => info.hasPrompt);
    if (hasPromptNodes && !persons.length) {
      needDefault = true;
    }

    // Check if any prompt nodes don't have matching agents
    Object.entries(nodeInfo).forEach(([name, info]) => {
      if (info.hasPrompt && !agentsData[name]) {
        needDefault = true;
      }
    });

    if (needDefault) {
      persons.push(defaultPerson);
      this.personMap['_default'] = defaultPersonId;
    }

    return persons;
  }

  private extractApiKeys(persons: PersonDefinition[]): ApiKey[] {
    const apiKeys: Record<string, ApiKey> = {};

    persons.forEach(person => {
      const service = person.service || 'openai';
      if (!apiKeys[service]) {
        const apiKeyId = `APIKEY_${nanoid(6)}`;
        apiKeys[service] = {
          id: apiKeyId,
          name: `${service.charAt(0).toUpperCase() + service.slice(1)} API Key`,
          service: service as any
        };
      }
    });

    // Update persons with API key IDs
    persons.forEach(person => {
      const service = person.service || 'openai';
      person.apiKeyId = apiKeys[service]?.id;
    });

    return Object.values(apiKeys);
  }

  private linkPersonsToNodes(nodes: DiagramNode[], nodeInfo: Record<string, NodeInfo>, data: LLMYamlFormat): void {
    nodes.forEach(node => {
      // Find original name from nodeMap
      const originalName = Object.entries(this.nodeMap).find(([, id]) => id === node.id)?.[0];
      if (!originalName) return;

      const info = nodeInfo[originalName];
      if (info?.type === 'person_job' && node.data.type === 'person_job') {
        const nodeData = node.data as PersonJobBlockData;
        
        // Check if this node has a specific agent
        if (data.agents?.[originalName]) {
          nodeData.personId = this.personMap[originalName];
        } else if (info.hasPrompt) {
          // Use default person
          nodeData.personId = this.personMap['_default'];
        }
      }
    });
  }

  private calculatePositions(nodeInfo: Record<string, NodeInfo>): Record<string, { x: number; y: number }> {
    const positions: Record<string, { x: number; y: number }> = {};

    // Find start nodes or nodes with no incoming edges
    const startNodes = Object.entries(nodeInfo)
      .filter(([_name, info]) => info.type === 'start' || info.incoming.length === 0)
      .map(([name]) => name);

    if (startNodes.length === 0 && Object.keys(nodeInfo).length > 0) {
      startNodes.push(Object.keys(nodeInfo)[0] || '');
    }

    // BFS layout
    const visited = new Set<string>();
    const queue: Array<{ node: string; level: number; index: number }> = 
      startNodes.map((node, i) => ({ node, level: 0, index: i }));
    const levelCounts: Record<number, number> = {};

    while (queue.length > 0) {
      const { node, level, index } = queue.shift()!;
      if (visited.has(node)) continue;

      visited.add(node);

      // Position calculation
      positions[node] = {
        x: level * 250,
        y: index * 150
      };

      // Queue children
      const info = nodeInfo[node];
      if (info) {
        const children = info.outgoing.map(e => e.target);
        children.forEach(child => {
          if (!visited.has(child)) {
            const nextLevel = level + 1;
            levelCounts[nextLevel] = (levelCounts[nextLevel] || 0) + 1;
            queue.push({
              node: child,
              level: nextLevel,
              index: levelCounts[nextLevel] - 1
            });
          }
        });
      }
    }

    return positions;
  }

  private nodeTypeToId(nodeType: string): string {
    const mapping: Record<string, string> = {
      start: 'start',
      endpoint: 'endpoint',
      personjob: 'person_job',
      condition: 'condition',
      db: 'db',
      job: 'job',
      generic: 'person_job'
    };
    return mapping[nodeType] || 'person_job';
  }

  private detectVariables(prompt: string): string[] {
    const vars = new Set<string>();
    const varPattern = /{{(\w+)}}/g;
    
    const matches = prompt.matchAll(varPattern);
    for (const match of matches) {
      vars.add(match[1] || '');
    }
    
    return Array.from(vars);
  }

  /**
   * Export DiagramState to LLM-friendly YAML format
   */
  private exportYaml(diagram: DiagramState): string {
    const flow: string[] = [];
    const prompts: Record<string, string> = {};
    const agents: Record<string, any> = {};
    const data: Record<string, string> = {};

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
        nodeName = node.data.label.replace(/\s+/g, '_').toLowerCase();
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
      const personName = person.label?.replace(/\s+/g, '_').toLowerCase() || `agent_${index + 1}`;
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
        const nodeData = node.data as PersonJobBlockData;
        if (nodeData.defaultPrompt) {
          prompts[nodeName] = nodeData.defaultPrompt;
        }
      } else if (nodeName && node.type === 'db' && node.data.type === 'db') {
        const dbData = node.data as DBBlockData;
        if (dbData.sourceDetails) {
          data[nodeName] = dbData.sourceDetails;
        }
      }
    });

    // Extract agents from persons
    diagram.persons.forEach(person => {
      const personName = personNameMap[person.id];
      
      if (personName && (person.systemPrompt || person.modelName !== 'gpt-4' || person.service !== 'openai')) {
        const agent: any = {};
        
        if (person.modelName && person.modelName !== 'gpt-4') {
          agent.model = person.modelName;
        }
        if (person.service && person.service !== 'openai') {
          agent.service = person.service;
        }
        if (person.systemPrompt) {
          agent.system = person.systemPrompt;
        }

        // Simplify if only system prompt
        if (Object.keys(agent).length === 1 && agent.system) {
          agents[personName] = agent.system;
        } else {
          agents[personName] = agent;
        }
      }
    });

    // Build final YAML structure
    const yamlData: any = {
      flow
    };

    if (Object.keys(prompts).length > 0) {
      yamlData.prompts = prompts;
    }

    if (Object.keys(agents).length > 0) {
      yamlData.agents = agents;
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