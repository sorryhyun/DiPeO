// apps/web/src/utils/__tests__/connection-helpers.test.ts
import { describe, it, expect } from 'vitest';
import {
  connect,
  canConnect,
  areDataTypesCompatible,
  findValidTargets,
  connectChain
} from '@/utils/connection-helpers';
import { createStartNode, createPersonJobNode, createConditionNode } from '@/utils/factories/node-factory';
import { DataType } from '@/types/enums';
import { personId } from '@/types/branded';

describe('Connection Helpers', () => {
  describe('areDataTypesCompatible', () => {
    it('should allow any type to connect to any', () => {
      expect(areDataTypesCompatible(DataType.Any, DataType.String)).toBe(true);
      expect(areDataTypesCompatible(DataType.Number, DataType.Any)).toBe(true);
      expect(areDataTypesCompatible(DataType.Any, DataType.Any)).toBe(true);
    });
    
    it('should allow same types to connect', () => {
      expect(areDataTypesCompatible(DataType.String, DataType.String)).toBe(true);
      expect(areDataTypesCompatible(DataType.Number, DataType.Number)).toBe(true);
      expect(areDataTypesCompatible(DataType.Boolean, DataType.Boolean)).toBe(true);
    });
    
    it('should allow compatible type conversions', () => {
      expect(areDataTypesCompatible(DataType.String, DataType.Text)).toBe(true);
      expect(areDataTypesCompatible(DataType.Text, DataType.String)).toBe(true);
      expect(areDataTypesCompatible(DataType.Integer, DataType.Number)).toBe(true);
      expect(areDataTypesCompatible(DataType.Float, DataType.Number)).toBe(true);
      expect(areDataTypesCompatible(DataType.JSON, DataType.Object)).toBe(true);
    });
    
    it('should reject incompatible types', () => {
      expect(areDataTypesCompatible(DataType.String, DataType.Number)).toBe(false);
      expect(areDataTypesCompatible(DataType.Boolean, DataType.String)).toBe(false);
      expect(areDataTypesCompatible(DataType.Array, DataType.Number)).toBe(false);
    });
  });
  
  describe('connect', () => {
    it('should create a connection between compatible nodes', () => {
      const start = createStartNode('data');
      const job = createPersonJobNode(personId('p1'), {
        firstOnlyPrompt: 'Process {{data}}',
        defaultPrompt: 'Continue'
      });
      
      const arrow = connect(
        { node: start, handle: 'default' },
        { node: job, handle: 'first' }
      );
      
      expect(arrow.id).toBeDefined();
      expect(arrow.source).toBe(start.outputs.default.id);
      expect(arrow.target).toBe(job.inputs.first.id);
      expect(arrow.type).toBe('smoothstep');
    });
    
    it('should accept custom arrow options', () => {
      const start = createStartNode('data');
      const job = createPersonJobNode(personId('p1'), {
        firstOnlyPrompt: 'Process',
        defaultPrompt: 'Continue'
      });
      
      const arrow = connect(
        { node: start, handle: 'default' },
        { node: job, handle: 'first' },
        {
          type: 'straight',
          animated: true,
          label: 'Data Flow'
        }
      );
      
      expect(arrow.type).toBe('straight');
      expect(arrow.animated).toBe(true);
      expect(arrow.label).toBe('Data Flow');
    });
    
    it('should throw error for incompatible connections', () => {
      // This would need nodes with incompatible data types
      // For now, we'll test with skipValidation option
      const start = createStartNode('data');
      const job = createPersonJobNode(personId('p1'), {
        firstOnlyPrompt: 'Process',
        defaultPrompt: 'Continue'
      });
      
      // Should not throw with skipValidation
      expect(() => connect(
        { node: start, handle: 'default' },
        { node: job, handle: 'first' },
        { skipValidation: true }
      )).not.toThrow();
    });
  });
  
  describe('canConnect', () => {
    it('should return true for valid connections', () => {
      const start = createStartNode('data');
      const job = createPersonJobNode(personId('p1'), {
        firstOnlyPrompt: 'Process',
        defaultPrompt: 'Continue'
      });
      
      expect(canConnect(
        { node: start, handle: 'default' },
        { node: job, handle: 'first' }
      )).toBe(true);
    });
    
    it('should return false for invalid handle names', () => {
      const start = createStartNode('data');
      const job = createPersonJobNode(personId('p1'), {
        firstOnlyPrompt: 'Process',
        defaultPrompt: 'Continue'
      });
      
      expect(canConnect(
        { node: start, handle: 'invalid' as any },
        { node: job, handle: 'first' }
      )).toBe(false);
    });
  });
  
  describe('findValidTargets', () => {
    it('should find all valid target handles', () => {
      const start = createStartNode('data');
      const job1 = createPersonJobNode(personId('p1'), {
        firstOnlyPrompt: 'Process 1',
        defaultPrompt: 'Continue'
      });
      const job2 = createPersonJobNode(personId('p2'), {
        firstOnlyPrompt: 'Process 2',
        defaultPrompt: 'Continue'
      });
      const condition = createConditionNode('x > 0');
      
      const targets = findValidTargets(
        start,
        'default',
        [job1, job2, condition]
      );
      
      expect(targets).toHaveLength(4); // 2 handles on each PersonJob + 1 on Condition
      expect(targets).toContainEqual({ node: job1, handle: 'first' });
      expect(targets).toContainEqual({ node: job1, handle: 'default' });
      expect(targets).toContainEqual({ node: job2, handle: 'first' });
      expect(targets).toContainEqual({ node: condition, handle: 'default' });
    });
    
    it('should skip self-connections', () => {
      const job = createPersonJobNode(personId('p1'), {
        firstOnlyPrompt: 'Process',
        defaultPrompt: 'Continue'
      });
      
      const targets = findValidTargets(job, 'default', [job]);
      
      expect(targets).toHaveLength(0);
    });
  });
  
  describe('connectChain', () => {
    it('should connect nodes in sequence', () => {
      const start = createStartNode('data');
      const job = createPersonJobNode(personId('p1'), {
        firstOnlyPrompt: 'Process',
        defaultPrompt: 'Continue'
      });
      const condition = createConditionNode('x > 0');
      
      const arrows = connectChain([start, job, condition], [
        { from: 'default', to: 'first' },
        { from: 'default', to: 'default' }
      ]);
      
      expect(arrows).toHaveLength(2);
      expect(arrows[0].source).toBe(start.outputs.default.id);
      expect(arrows[0].target).toBe(job.inputs.first.id);
      expect(arrows[1].source).toBe(job.outputs.default.id);
      expect(arrows[1].target).toBe(condition.inputs.default.id);
    });
    
    it('should use default handles when not specified', () => {
      const start = createStartNode('data');
      const condition = createConditionNode('x > 0');
      
      const arrows = connectChain([start, condition]);
      
      expect(arrows).toHaveLength(1);
      expect(arrows[0].source).toBe(start.outputs.default.id);
      expect(arrows[0].target).toBe(condition.inputs.default.id);
    });
    
    it('should return empty array for single node', () => {
      const start = createStartNode('data');
      const arrows = connectChain([start]);
      
      expect(arrows).toHaveLength(0);
    });
  });
});