/**
 * Dispatch Table Utilities
 * 
 * Provides a type-safe dispatch table pattern to replace switch statements
 * with more maintainable and performant lookup tables.
 */

/**
 * Generic dispatch table type
 */
export type DispatchTable<TKey extends string | number | symbol, TValue> = Record<TKey, TValue>;

/**
 * Function dispatch table for handlers
 */
export type HandlerTable<TKey extends string | number | symbol, TArgs extends unknown[], TReturn> = 
  DispatchTable<TKey, (...args: TArgs) => TReturn>;

/**
 * Creates a type-safe dispatch table with optional default handler
 */
export function createDispatchTable<
  TKey extends string | number | symbol,
  TValue
>(
  entries: DispatchTable<TKey, TValue>,
  defaultValue?: TValue
): {
  get: (key: TKey) => TValue | undefined;
  has: (key: TKey) => boolean;
  getOrDefault: (key: TKey) => TValue;
} {
  return {
    get: (key: TKey) => entries[key],
    has: (key: TKey) => key in entries,
    getOrDefault: (key: TKey) => entries[key] ?? defaultValue!
  };
}

/**
 * Creates a handler dispatch table with type-safe execution
 */
export function createHandlerTable<
  TKey extends string | number | symbol,
  TArgs extends unknown[],
  TReturn
>(
  handlers: HandlerTable<TKey, TArgs, TReturn>,
  defaultHandler?: (...args: TArgs) => TReturn
): {
  execute: (key: TKey, ...args: TArgs) => TReturn | undefined;
  executeOrDefault: (key: TKey, ...args: TArgs) => TReturn;
  has: (key: TKey) => boolean;
} {
  return {
    execute: (key: TKey, ...args: TArgs) => {
      const handler = handlers[key];
      return handler ? handler(...args) : undefined;
    },
    executeOrDefault: (key: TKey, ...args: TArgs) => {
      const handler = handlers[key];
      if (handler) return handler(...args);
      if (defaultHandler) return defaultHandler(...args);
      throw new Error(`No handler found for key: ${String(key)}`);
    },
    has: (key: TKey) => key in handlers
  };
}

/**
 * Creates a lookup table for simple value mappings
 */
export function createLookupTable<
  TKey extends string | number | symbol,
  TValue
>(
  entries: DispatchTable<TKey, TValue>
): (key: TKey) => TValue | undefined {
  return (key: TKey) => entries[key];
}

/**
 * Type guard for checking if a key exists in a dispatch table
 */
export function isValidTableKey<TKey extends string | number | symbol>(
  key: unknown,
  table: DispatchTable<TKey, unknown>
): key is TKey {
  return typeof key === 'string' && key in table;
}