import { useMemo } from 'react';

/**
 * Generic hook to find an entity by ID and transform it
 * @param entityId - The ID of the entity to find
 * @param entities - Array of entities to search in
 * @param transformer - Optional function to transform the found entity
 * @returns The transformed entity or null if not found
 */
export function useEntityById<T extends { id: string }, R = T>(
  entityId: string | null | undefined,
  entities: T[] | undefined,
  transformer?: (entity: T) => R
): R | null {
  return useMemo(() => {
    if (!entityId || !entities) return null;
    
    const entity = entities.find(e => e.id === entityId);
    if (!entity) return null;
    
    return transformer ? transformer(entity) : (entity as unknown as R);
  }, [entityId, entities, transformer]);
}

/**
 * Specialized hook for finding entities with additional context
 * Useful when the transformation requires additional data from other sources
 */
export function useEntityByIdWithContext<
  T extends { id: string },
  C,
  R = T
>(
  entityId: string | null | undefined,
  entities: T[] | undefined,
  context: C,
  transformer: (entity: T, context: C) => R
): R | null {
  return useMemo(() => {
    if (!entityId || !entities) return null;
    
    const entity = entities.find(e => e.id === entityId);
    if (!entity) return null;
    
    return transformer(entity, context);
  }, [entityId, entities, context, transformer]);
}