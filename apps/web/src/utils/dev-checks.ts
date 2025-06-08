/**
 * Development-only runtime checks and assertions
 * These are stripped out in production builds for zero overhead
 */

import { isNodeId, isHandleId, isArrowId, isPersonId } from '@/types/branded';

/**
 * Development assertion that logs error and breaks into debugger
 * @param condition - Condition to check
 * @param message - Error message if condition is false
 */
export function devAssert(condition: boolean, message: string): void {
  if (import.meta.env.DEV && !condition) {
    console.error(`Development assertion failed: ${message}`);
    console.trace();
    debugger; // This will be stripped in production
  }
}

/**
 * Development warning that logs but doesn't break
 * @param condition - Condition to check
 * @param message - Warning message if condition is false
 */
export function devWarn(condition: boolean, message: string): void {
  if (import.meta.env.DEV && !condition) {
    console.warn(`Development warning: ${message}`);
  }
}

/**
 * Log detailed information in development only
 * @param label - Label for the log
 * @param data - Data to log
 */
export function devLog(label: string, data?: unknown): void {
  if (import.meta.env.DEV) {
    console.log(`[DEV] ${label}`, data);
  }
}

/**
 * Performance measurement in development only
 * @param label - Label for the measurement
 * @param fn - Function to measure
 * @returns Result of the function
 */
export function devMeasure<T>(label: string, fn: () => T): T {
  if (import.meta.env.DEV) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    console.log(`[PERF] ${label}: ${(end - start).toFixed(2)}ms`);
    return result;
  }
  return fn();
}

/**
 * Type validation assertions for development
 */
export const devTypeChecks = {
  assertNodeId(id: string, context?: string): void {
    devAssert(
      isNodeId(id),
      `Invalid NodeID format: ${id}${context ? ` (${context})` : ''}`
    );
  },
  
  assertHandleId(id: string, context?: string): void {
    devAssert(
      isHandleId(id),
      `Invalid HandleID format: ${id}${context ? ` (${context})` : ''}`
    );
  },
  
  assertArrowId(id: string, context?: string): void {
    devAssert(
      isArrowId(id),
      `Invalid ArrowID format: ${id}${context ? ` (${context})` : ''}`
    );
  },
  
  assertPersonId(id: string, context?: string): void {
    devAssert(
      isPersonId(id),
      `Invalid PersonID format: ${id}${context ? ` (${context})` : ''}`
    );
  },
  
  assertValidConnection(
    sourceNodeType: string,
    sourceHandle: string,
    targetNodeType: string,
    targetHandle: string
  ): void {
    devAssert(
      sourceNodeType && sourceHandle && targetNodeType && targetHandle,
      `Invalid connection: ${sourceNodeType}:${sourceHandle} -> ${targetNodeType}:${targetHandle}`
    );
  },
};

/**
 * Validate object shape in development
 */
export function devValidateShape<T extends object>(
  obj: unknown,
  shape: Record<keyof T, (val: unknown) => boolean>,
  label: string
): void {
  if (!import.meta.env.DEV) return;
  
  if (!obj || typeof obj !== 'object') {
    console.error(`${label}: Expected object, got ${typeof obj}`);
    return;
  }
  
  const objRecord = obj as Record<string, unknown>;
  
  for (const [key, validator] of Object.entries(shape)) {
    if (!validator(objRecord[key])) {
      console.error(`${label}: Invalid value for key '${key}'`, objRecord[key]);
    }
  }
}

/**
 * Check for potential memory leaks in development
 */
export class DevMemoryMonitor {
  private static instances = new Map<string, number>();
  
  static register(name: string): void {
    if (!import.meta.env.DEV) return;
    
    const count = this.instances.get(name) || 0;
    this.instances.set(name, count + 1);
    
    if (count > 10) {
      console.warn(`Potential memory leak: ${name} has ${count + 1} instances`);
    }
  }
  
  static unregister(name: string): void {
    if (!import.meta.env.DEV) return;
    
    const count = this.instances.get(name) || 0;
    if (count > 0) {
      this.instances.set(name, count - 1);
    }
  }
  
  static report(): void {
    if (!import.meta.env.DEV) return;
    
    console.table(
      Array.from(this.instances.entries())
        .filter(([_, count]) => count > 0)
        .map(([name, count]) => ({ Component: name, Instances: count }))
    );
  }
}

// Export a no-op version for production to avoid bundling
export const prodChecks = {
  devAssert: () => {},
  devWarn: () => {},
  devLog: () => {},
  devMeasure: <T>(label: string, fn: () => T) => fn(),
  devTypeChecks: {
    assertNodeId: () => {},
    assertHandleId: () => {},
    assertArrowId: () => {},
    assertPersonId: () => {},
    assertValidConnection: () => {},
  },
  devValidateShape: () => {},
  DevMemoryMonitor: {
    register: () => {},
    unregister: () => {},
    report: () => {},
  },
};

// Use this in production builds
export default import.meta.env.DEV ? {
  devAssert,
  devWarn,
  devLog,
  devMeasure,
  devTypeChecks,
  devValidateShape,
  DevMemoryMonitor,
} : prodChecks;