/**
 * Arrow Converter Module
 *
 * Handles all conversions related to diagram arrows (connections).
 * Manages transformations between different arrow representations.
 */

import {
  type ArrowID,
  type HandleID,
  type DomainArrow,
  type ContentType
} from '@dipeo/models';
import type { DomainArrowType } from '@/__generated__/graphql';
import { arrowId, handleId } from '@/infrastructure/types/branded';

export class ArrowConverter {
  /**
   * Convert GraphQL arrow to domain arrow
   */
  static toDomain(graphqlArrow: DomainArrowType): DomainArrow {
    return {
      id: arrowId(graphqlArrow.id),
      source: handleId(graphqlArrow.source),
      target: handleId(graphqlArrow.target),
      content_type: (graphqlArrow.content_type as unknown as ContentType) || null,
      label: graphqlArrow.label || null,
      data: graphqlArrow.data || null
    };
  }

  /**
   * Convert domain arrow to GraphQL input
   */
  static toGraphQL(domainArrow: DomainArrow): Partial<DomainArrowType> {
    return {
      id: domainArrow.id,
      source: domainArrow.source,
      target: domainArrow.target,
      content_type: domainArrow.content_type as string | null,
      label: domainArrow.label,
      data: domainArrow.data
    };
  }

  /**
   * Batch convert GraphQL arrows to domain
   */
  static batchToDomain(graphqlArrows: DomainArrowType[]): DomainArrow[] {
    return graphqlArrows.map(arrow => this.toDomain(arrow));
  }

  /**
   * Batch convert domain arrows to GraphQL
   */
  static batchToGraphQL(domainArrows: DomainArrow[]): Partial<DomainArrowType>[] {
    return domainArrows.map(arrow => this.toGraphQL(arrow));
  }

  /**
   * Convert array to Map for efficient lookups
   */
  static arrayToMap(arrows: DomainArrow[]): Map<ArrowID, DomainArrow> {
    return new Map(arrows.map(arrow => [arrow.id, arrow]));
  }

  /**
   * Find arrows connected to a specific handle
   */
  static findByHandle(arrows: DomainArrow[], handleId: HandleID): {
    incoming: DomainArrow[];
    outgoing: DomainArrow[];
  } {
    const incoming = arrows.filter(arrow => arrow.target === handleId);
    const outgoing = arrows.filter(arrow => arrow.source === handleId);
    return { incoming, outgoing };
  }

  /**
   * Find arrows between two nodes (via their handles)
   */
  static findBetweenHandles(
    arrows: DomainArrow[],
    sourceHandles: HandleID[],
    targetHandles: HandleID[]
  ): DomainArrow[] {
    const sourceSet = new Set(sourceHandles);
    const targetSet = new Set(targetHandles);
    return arrows.filter(arrow =>
      sourceSet.has(arrow.source) && targetSet.has(arrow.target)
    );
  }

  /**
   * Create arrow ID from source and target handles
   */
  static createArrowId(source: HandleID, target: HandleID): ArrowID {
    return arrowId(`${source}_to_${target}`);
  }

  /**
   * Create a minimal arrow
   */
  static createArrow(source: HandleID, target: HandleID): DomainArrow {
    return {
      id: this.createArrowId(source, target),
      source,
      target,
      content_type: null,
      label: null,
      data: null
    };
  }
}
