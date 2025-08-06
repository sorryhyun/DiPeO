/**
 * Diagram Converter Module
 * 
 * Handles conversions for complete diagrams.
 * Orchestrates conversions of all diagram components.
 */

import {
  type NodeID,
  type ArrowID,
  type HandleID,
  type PersonID,
  type DiagramID,
  type DomainDiagram,
  type DomainNode,
  type DomainArrow,
  type DomainHandle,
  type DomainPerson,
  type DiagramMetadata,
  diagramArraysToMaps,
  diagramMapsToArrays,
  convertGraphQLDiagramToDomain
} from '@dipeo/models';
import type { DomainDiagramType } from '@/__generated__/graphql';
import { diagramId } from '@/infrastructure/types/branded';
import { NodeConverter } from './node-converter';
import { ArrowConverter } from './arrow-converter';
import { HandleConverter } from './handle-converter';
import { PersonConverter } from './person-converter';

export interface DiagramMaps {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  handles: Map<HandleID, DomainHandle>;
  persons: Map<PersonID, DomainPerson>;
  metadata?: DiagramMetadata;
}

export class DiagramConverter {
  /**
   * Convert GraphQL diagram to domain diagram
   * Uses utility from @dipeo/models
   */
  static toDomain(graphqlDiagram: DomainDiagramType | any): Partial<DomainDiagram> {
    return convertGraphQLDiagramToDomain(graphqlDiagram);
  }
  
  /**
   * Convert domain diagram to GraphQL input
   */
  static toGraphQL(domainDiagram: Partial<DomainDiagram>): Partial<DomainDiagramType> {
    const result: Partial<DomainDiagramType> = {};
    
    if (domainDiagram.nodes) {
      result.nodes = NodeConverter.batchToGraphQL(domainDiagram.nodes) as any;
    }
    
    if (domainDiagram.arrows) {
      result.arrows = ArrowConverter.batchToGraphQL(domainDiagram.arrows) as any;
    }
    
    if (domainDiagram.handles) {
      result.handles = HandleConverter.batchToGraphQL(domainDiagram.handles) as any;
    }
    
    if (domainDiagram.persons) {
      result.persons = PersonConverter.batchToGraphQL(domainDiagram.persons) as any;
    }
    
    if (domainDiagram.metadata) {
      result.metadata = domainDiagram.metadata as any;
    }
    
    return result;
  }
  
  /**
   * Convert GraphQL diagram to domain with Maps
   */
  static toDomainMaps(graphqlDiagram: DomainDiagramType): DiagramMaps {
    const domainDiagram = this.toDomain(graphqlDiagram);
    const maps = diagramArraysToMaps(domainDiagram);
    
    return {
      ...maps,
      metadata: graphqlDiagram.metadata as DiagramMetadata | undefined
    };
  }
  
  /**
   * Convert diagram arrays to Maps for efficient operations
   */
  static arraysToMaps(diagram: Partial<DomainDiagram>): DiagramMaps {
    const maps = diagramArraysToMaps(diagram);
    return {
      ...maps,
      metadata: diagram.metadata || undefined
    };
  }
  
  /**
   * Convert diagram Maps back to arrays for storage
   */
  static mapsToArrays(maps: DiagramMaps): DomainDiagram {
    const arrays = diagramMapsToArrays(maps);
    return {
      ...arrays,
      metadata: maps.metadata || {
        id: diagramId(''),
        name: 'Untitled',
        description: null,
        version: '1.0.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString()
      }
    } as DomainDiagram;
  }
  
  /**
   * Create an empty diagram
   */
  static createEmpty(name: string = 'Untitled'): DomainDiagram {
    return {
      nodes: [],
      arrows: [],
      handles: [],
      persons: [],
      metadata: {
        id: diagramId(`diagram_${Date.now()}`),
        name,
        description: null,
        version: '1.0.0',
        created: new Date().toISOString(),
        modified: new Date().toISOString()
      }
    };
  }
  
  /**
   * Merge two diagrams
   */
  static merge(
    diagram1: Partial<DomainDiagram>,
    diagram2: Partial<DomainDiagram>
  ): Partial<DomainDiagram> {
    return {
      nodes: [...(diagram1.nodes || []), ...(diagram2.nodes || [])],
      arrows: [...(diagram1.arrows || []), ...(diagram2.arrows || [])],
      handles: [...(diagram1.handles || []), ...(diagram2.handles || [])],
      persons: [...(diagram1.persons || []), ...(diagram2.persons || [])],
      metadata: diagram1.metadata || diagram2.metadata
    };
  }
  
  /**
   * Validate diagram structure
   */
  static validate(diagram: Partial<DomainDiagram>): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];
    
    // Check for orphaned handles
    if (diagram.handles && diagram.nodes) {
      const nodeIds = new Set(diagram.nodes.map(n => n.id));
      const orphanedHandles = diagram.handles.filter(h => !nodeIds.has(h.node_id));
      if (orphanedHandles.length > 0) {
        errors.push(`Found ${orphanedHandles.length} orphaned handles`);
      }
    }
    
    // Check for invalid arrows
    if (diagram.arrows && diagram.handles) {
      const handleIds = new Set(diagram.handles.map(h => h.id));
      const invalidArrows = diagram.arrows.filter(a => 
        !handleIds.has(a.source) || !handleIds.has(a.target)
      );
      if (invalidArrows.length > 0) {
        errors.push(`Found ${invalidArrows.length} arrows with invalid handles`);
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
}