/**
 * Tests for the typed connection system
 */

import { describe, it, expect } from 'vitest';
import { createConnection, validateConnection, findValidTargets, findValidSources } from '../typed-connection';
import { legacyNodeToDiagramNode, diagramNodeToLegacyNode } from '../diagram-bridge';
import { NodeType, DataType, ArrowType } from '@/types/enums';
import { DiagramNode } from '@/types/diagram';
import { generateId } from '@/utils/id';
import type { Node, Handle } from '@/types';

describe('Typed Connection System', () => {
  // Helper to create a test node
  const createTestNode = (type: NodeType, id: string): Node => {
    const handles: Handle[] = [];
    
    // Add handles based on node type
    switch (type) {
      case NodeType.Start:
        handles.push({
          id: `${id}:default`,
          kind: 'source',
          name: 'default',
          dataType: 'any',
          position: { x: 0, y: 0 }
        });
        break;
      case NodeType.PersonJob:
        handles.push(
          {
            id: `${id}:first`,
            kind: 'target',
            name: 'first',
            dataType: 'any',
            position: { x: 0, y: 0 }
          },
          {
            id: `${id}:default`,
            kind: 'target',
            name: 'default',
            dataType: 'any',
            position: { x: 0, y: 0 }
          },
          {
            id: `${id}:output`,
            kind: 'source',
            name: 'output',
            dataType: 'any',
            position: { x: 0, y: 0 }
          }
        );
        break;
      case NodeType.Endpoint:
        handles.push({
          id: `${id}:default`,
          kind: 'target',
          name: 'default',
          dataType: 'any',
          position: { x: 0, y: 0 }
        });
        break;
    }
    
    return {
      id,
      type: type.toLowerCase().replace('_', ''),
      position: { x: 0, y: 0 },
      data: { type: type.toLowerCase().replace('_', ''), id },
      handles
    } as Node;
  };

  describe('Node Conversion', () => {
    it('should convert legacy node to diagram node', () => {
      const legacyNode = createTestNode(NodeType.Start, 'start-1');
      const diagramNode = legacyNodeToDiagramNode(legacyNode);
      
      expect(diagramNode.type).toBe(NodeType.Start);
      expect(Object.keys(diagramNode.outputs)).toContain('default');
      expect(Object.keys(diagramNode.inputs)).toHaveLength(0);
    });

    it('should convert diagram node back to legacy node', () => {
      const legacyNode = createTestNode(NodeType.PersonJob, 'person-1');
      const diagramNode = legacyNodeToDiagramNode(legacyNode);
      const convertedBack = diagramNodeToLegacyNode(diagramNode);
      
      expect(convertedBack.type).toBe('person_job');
      expect(convertedBack.handles).toHaveLength(3);
    });
  });

  describe('Connection Creation', () => {
    it('should create valid connection between compatible nodes', () => {
      const startNode = legacyNodeToDiagramNode(createTestNode(NodeType.Start, 'start-1'));
      const personNode = legacyNodeToDiagramNode(createTestNode(NodeType.PersonJob, 'person-1'));
      
      const connection = createConnection(
        startNode as any,
        'default',
        personNode as any,
        'first'
      );
      
      expect(connection.source).toBe('start-1:default');
      expect(connection.target).toBe('person-1:first');
      expect(connection.type).toBe(ArrowType.SmoothStep);
    });

    it('should throw error for invalid output handle', () => {
      const startNode = legacyNodeToDiagramNode(createTestNode(NodeType.Start, 'start-1'));
      const personNode = legacyNodeToDiagramNode(createTestNode(NodeType.PersonJob, 'person-1'));
      
      expect(() => {
        createConnection(
          startNode as any,
          'invalid',
          personNode as any,
          'first'
        );
      }).toThrow('Output handle "invalid" not found');
    });
  });

  describe('Connection Validation', () => {
    it('should validate existing connections', () => {
      const nodes = new Map<string, DiagramNode>();
      const startNode = legacyNodeToDiagramNode(createTestNode(NodeType.Start, 'start-1'));
      const personNode = legacyNodeToDiagramNode(createTestNode(NodeType.PersonJob, 'person-1'));
      
      nodes.set('start-1', startNode);
      nodes.set('person-1', personNode);
      
      const arrow = {
        id: generateId('arrow'),
        source: 'start-1:default',
        target: 'person-1:first'
      };
      
      const result = validateConnection(arrow as any, nodes);
      expect(result.valid).toBe(true);
    });

    it('should reject invalid connections', () => {
      const nodes = new Map<string, DiagramNode>();
      const startNode = legacyNodeToDiagramNode(createTestNode(NodeType.Start, 'start-1'));
      nodes.set('start-1', startNode);
      
      const arrow = {
        id: generateId('arrow'),
        source: 'start-1:default',
        target: 'nonexistent:handle'
      };
      
      const result = validateConnection(arrow as any, nodes);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('not found');
    });
  });

  describe('Finding Valid Connections', () => {
    it('should find valid targets for a source handle', () => {
      const nodes = new Map<string, DiagramNode>();
      const startNode = legacyNodeToDiagramNode(createTestNode(NodeType.Start, 'start-1'));
      const personNode = legacyNodeToDiagramNode(createTestNode(NodeType.PersonJob, 'person-1'));
      const endpointNode = legacyNodeToDiagramNode(createTestNode(NodeType.Endpoint, 'endpoint-1'));
      
      nodes.set('start-1', startNode);
      nodes.set('person-1', personNode);
      nodes.set('endpoint-1', endpointNode);
      
      const targets = findValidTargets('start-1', 'default', nodes);
      
      expect(targets).toHaveLength(3); // person-1:first, person-1:default, endpoint-1:default
      expect(targets.some(t => t.nodeId === 'person-1' && t.handleName === 'first')).toBe(true);
      expect(targets.some(t => t.nodeId === 'endpoint-1' && t.handleName === 'default')).toBe(true);
    });

    it('should find valid sources for a target handle', () => {
      const nodes = new Map<string, DiagramNode>();
      const startNode = legacyNodeToDiagramNode(createTestNode(NodeType.Start, 'start-1'));
      const personNode = legacyNodeToDiagramNode(createTestNode(NodeType.PersonJob, 'person-1'));
      const endpointNode = legacyNodeToDiagramNode(createTestNode(NodeType.Endpoint, 'endpoint-1'));
      
      nodes.set('start-1', startNode);
      nodes.set('person-1', personNode);
      nodes.set('endpoint-1', endpointNode);
      
      const sources = findValidSources('endpoint-1', 'default', nodes);
      
      expect(sources).toHaveLength(2); // start-1:default, person-1:output
      expect(sources.some(s => s.nodeId === 'start-1' && s.handleName === 'default')).toBe(true);
      expect(sources.some(s => s.nodeId === 'person-1' && s.handleName === 'output')).toBe(true);
    });
  });
});