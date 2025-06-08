// apps/web/src/utils/__tests__/node-factory.test.ts
import { describe, it, expect } from 'vitest';
import {
  createNode,
  createStartNode,
  createPersonJobNode,
  createConditionNode,
  createEndpointNode
} from '@/utils/factories/node-factory';
import { NodeType } from '@/types/enums';
import { personId } from '@/types/branded';

describe('Node Factory', () => {
  describe('createNode', () => {
    it('should create a node with correct type and data', () => {
      const node = createNode(NodeType.Start, {
        output: 'test data'
      }, { x: 100, y: 200 });
      
      expect(node.type).toBe(NodeType.Start);
      expect(node.position).toEqual({ x: 100, y: 200 });
      expect(node.data.output).toBe('test data');
      expect(node.data.label).toBe('Start');
    });
    
    it('should generate unique node IDs', () => {
      const node1 = createNode(NodeType.Start, { output: 'data1' });
      const node2 = createNode(NodeType.Start, { output: 'data2' });
      
      expect(node1.id).not.toBe(node2.id);
      expect(node1.id).toMatch(/^st-/);
      expect(node2.id).toMatch(/^st-/);
    });
    
    it('should create handles based on node spec', () => {
      const node = createNode(NodeType.Condition, {
        condition: 'x > 5',
        conditionType: 'simple'
      });
      
      expect(node.inputs.default).toBeDefined();
      expect(node.outputs.true).toBeDefined();
      expect(node.outputs.false).toBeDefined();
    });
  });
  
  describe('createStartNode', () => {
    it('should create a start node with output handle only', () => {
      const node = createStartNode('{"data": "test"}', { x: 0, y: 0 }, 'My Start');
      
      expect(node.type).toBe(NodeType.Start);
      expect(node.data.output).toBe('{"data": "test"}');
      expect(node.data.label).toBe('My Start');
      expect(Object.keys(node.inputs)).toHaveLength(0);
      expect(Object.keys(node.outputs)).toHaveLength(1);
      expect(node.outputs.default).toBeDefined();
    });
  });
  
  describe('createPersonJobNode', () => {
    it('should create a person job node with correct handles', () => {
      const pId = personId('test-person');
      const node = createPersonJobNode(
        pId,
        {
          firstOnlyPrompt: 'First prompt',
          defaultPrompt: 'Default prompt'
        },
        {
          maxIteration: 5,
          contextCleaningRule: 'no_forget',
          position: { x: 100, y: 100 },
          label: 'My Job'
        }
      );
      
      expect(node.type).toBe(NodeType.PersonJob);
      expect(node.data.personId).toBe(pId);
      expect(node.data.firstOnlyPrompt).toBe('First prompt');
      expect(node.data.defaultPrompt).toBe('Default prompt');
      expect(node.data.maxIteration).toBe(5);
      expect(node.data.contextCleaningRule).toBe('no_forget');
      expect(node.data.label).toBe('My Job');
      
      // Check handles
      expect(node.inputs.first).toBeDefined();
      expect(node.inputs.default).toBeDefined();
      expect(node.outputs.default).toBeDefined();
    });
    
    it('should use default values when options not provided', () => {
      const pId = personId('test-person');
      const node = createPersonJobNode(pId, {
        firstOnlyPrompt: 'First',
        defaultPrompt: 'Default'
      });
      
      expect(node.data.maxIteration).toBe(1);
      expect(node.data.contextCleaningRule).toBe('no_forget');
      expect(node.position).toEqual({ x: 0, y: 0 });
    });
  });
  
  describe('createConditionNode', () => {
    it('should create a condition node with true/false outputs', () => {
      const node = createConditionNode(
        '{{value}} > 10',
        'simple',
        { x: 200, y: 200 },
        'Value Check'
      );
      
      expect(node.type).toBe(NodeType.Condition);
      expect(node.data.condition).toBe('{{value}} > 10');
      expect(node.data.conditionType).toBe('simple');
      expect(node.data.label).toBe('Value Check');
      
      // Check handles
      expect(node.inputs.default).toBeDefined();
      expect(node.outputs.true).toBeDefined();
      expect(node.outputs.false).toBeDefined();
      
      // Check handle positions
      expect(node.outputs.true.position.y).toBeLessThan(node.outputs.false.position.y);
    });
  });
  
  describe('createEndpointNode', () => {
    it('should create an endpoint node with input handle only', () => {
      const node = createEndpointNode(
        'save',
        'output.json',
        { x: 300, y: 300 },
        'Save Output'
      );
      
      expect(node.type).toBe(NodeType.Endpoint);
      expect(node.data.action).toBe('save');
      expect(node.data.filename).toBe('output.json');
      expect(node.data.label).toBe('Save Output');
      
      // Check handles
      expect(node.inputs.default).toBeDefined();
      expect(Object.keys(node.outputs)).toHaveLength(0);
    });
    
    it('should create output endpoint without filename', () => {
      const node = createEndpointNode('output');
      
      expect(node.data.action).toBe('output');
      expect(node.data.filename).toBeUndefined();
    });
  });
  
  describe('Node ID prefixes', () => {
    it('should use correct prefixes for each node type', () => {
      const nodes = [
        createStartNode('data'),
        createConditionNode('x > 0'),
        createPersonJobNode(personId('p1'), { firstOnlyPrompt: 'f', defaultPrompt: 'd' }),
        createEndpointNode('save')
      ];
      
      expect(nodes[0].id).toMatch(/^st-/);
      expect(nodes[1].id).toMatch(/^cd-/);
      expect(nodes[2].id).toMatch(/^pj-/);
      expect(nodes[3].id).toMatch(/^ep-/);
    });
  });
});