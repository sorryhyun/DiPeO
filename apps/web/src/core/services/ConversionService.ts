import { 
  parseHandleId as domainParseHandleId,
  createHandleId as domainCreateHandleId,
  type NodeID,
  type ArrowID,
  type PersonID,
  type HandleID
} from '@dipeo/domain-models';
import { nodeId, arrowId, personId, handleId } from '@/core/types/branded';

/**
 * Conversion Utilities Service
 * 
 * This service provides common utility functions to reduce code duplication
 * across the codebase for frequent conversion patterns.
 * 
 * Focus areas:
 * - ID type conversions and validation
 * - Common array/set/map transformations
 * - Data structure utilities
 */
export class ConversionService {
  // ===== ID Type Conversions =====
  
  /**
   * Safely cast string to NodeID
   * Reduces repetitive 'as NodeID' casting
   */
  static toNodeId(id: string): NodeID {
    return nodeId(id);
  }
  
  /**
   * Safely cast string to ArrowID
   * Reduces repetitive 'as ArrowID' casting
   */
  static toArrowId(id: string): ArrowID {
    return arrowId(id);
  }
  
  /**
   * Safely cast string to PersonID
   * Reduces repetitive 'as PersonID' casting
   */
  static toPersonId(id: string): PersonID {
    return personId(id);
  }
  
  /**
   * Safely cast string to HandleID
   * Reduces repetitive 'as HandleID' casting
   */
  static toHandleId(id: string): HandleID {
    return handleId(id);
  }
  
  // ===== Handle ID Operations =====
  
  /**
   * Parse handle ID into components
   * Centralizes handle ID parsing logic
   */
  static parseHandleId = domainParseHandleId;
  
  /**
   * Create handle ID from components
   * Centralizes handle ID creation logic
   */
  static createHandleId = domainCreateHandleId;
  
  // ===== Array/Set/Map Transformations =====
  
  /**
   * Convert array to Set of unique values based on property
   * Reduces repetitive pattern: new Set(array.map(item => item.prop).filter(Boolean))
   */
  static arrayToUniqueSet<T, K>(array: T[], selector: (item: T) => K | undefined): Set<K> {
    const values = array.map(selector).filter((value): value is K => value !== undefined && value !== null);
    return new Set(values);
  }
  
  /**
   * Convert array to Map keyed by property
   * Reduces repetitive reduce pattern
   */
  static arrayToMap<T, K extends string | number | symbol>(
    array: T[], 
    keySelector: (item: T) => K
  ): Map<K, T> {
    const map = new Map<K, T>();
    array.forEach(item => {
      map.set(keySelector(item), item);
    });
    return map;
  }
  
  /**
   * Convert array to object keyed by property
   * Reduces repetitive reduce pattern
   */
  static arrayToObject<T, K extends string | number>(
    array: T[], 
    keySelector: (item: T) => K
  ): Record<K, T> {
    return array.reduce((acc, item) => {
      acc[keySelector(item)] = item;
      return acc;
    }, {} as Record<K, T>);
  }
  
  /**
   * Map array with spread to add/modify properties
   * Reduces repetitive map spread pattern
   */
  static mapWithUpdate<T, U extends Partial<T>>(
    array: T[], 
    updater: (item: T) => U
  ): Array<T & U> {
    return array.map(item => ({ ...item, ...updater(item) }));
  }
  
  // ===== Collection Utilities =====
  
  /**
   * Check if collection is empty
   * Works with arrays, Maps, Sets, and objects
   */
  static isEmpty(collection: unknown): boolean {
    if (!collection) return true;
    if (Array.isArray(collection)) return collection.length === 0;
    if (collection instanceof Map || collection instanceof Set) return collection.size === 0;
    if (typeof collection === 'object') return Object.keys(collection).length === 0;
    return false;
  }
  
  /**
   * Get unique values from array
   */
  static unique<T>(array: T[]): T[] {
    return Array.from(new Set(array));
  }
  
  /**
   * Group array items by key
   */
  static groupBy<T, K extends string | number>(
    array: T[], 
    keySelector: (item: T) => K
  ): Record<K, T[]> {
    return array.reduce((groups, item) => {
      const key = keySelector(item);
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
      return groups;
    }, {} as Record<K, T[]>);
  }
  
  // ===== Data Transformations =====
  
  /**
   * Convert tools array to comma-separated string
   * Centralizes this common transformation
   */
  static toolsArrayToString(tools: Array<{ type: string }> | null | undefined): string {
    if (!tools || !Array.isArray(tools)) return '';
    return tools.map(tool => tool.type).join(', ');
  }
  
  /**
   * Convert comma-separated string to tools array
   * Centralizes this common transformation
   */
  static stringToToolsArray(toolsString: string): Array<{ type: string; enabled: boolean }> {
    if (!toolsString || !toolsString.trim()) return [];
    return toolsString.split(',').map(type => ({
      type: type.trim(),
      enabled: true
    }));
  }
}