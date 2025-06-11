/**
 * Utility types and helper types
 */

/**
 * Generic dictionary type
 */
export type Dict<V = unknown> = Record<string, V>;

/**
 * Nullable type helper
 */
export type Nullable<T> = T | null;

/**
 * Deep partial type helper
 */
export type DeepPartial<T> = { 
  [K in keyof T]?: DeepPartial<T[K]> 
};

/**
 * Deep readonly type helper
 */
export type DeepReadonly<T> = {
  readonly [K in keyof T]: DeepReadonly<T[K]>
};

/**
 * Extract function arguments
 */
export type ArgumentTypes<F extends (...args: any[]) => any> = F extends (...args: infer A) => any ? A : never;

/**
 * Extract function return type
 */
export type ReturnType<F extends (...args: any[]) => any> = F extends (...args: any[]) => infer R ? R : never;

/**
 * Omit multiple properties
 */
export type OmitMultiple<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

/**
 * Make specific properties optional
 */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/**
 * Make specific properties required
 */
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>;

/**
 * Union to intersection type helper
 */
export type UnionToIntersection<U> = (U extends any ? (k: U) => void : never) extends ((k: infer I) => void) ? I : never;

/**
 * Extract keys of specific value type
 */
export type KeysOfType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never
}[keyof T];

/**
 * Non-empty array type
 */
export type NonEmptyArray<T> = [T, ...T[]];

/**
 * Ensure at least one property is defined
 */
export type AtLeastOne<T, U = {[K in keyof T]: Pick<T, K>}> = Partial<T> & U[keyof U];

/**
 * Exclusive OR type - exactly one of the properties must be present
 */
export type XOR<T, U> = (T | U) extends object 
  ? (Without<T, U> & U) | (Without<U, T> & T)
  : T | U;

type Without<T, U> = { [P in Exclude<keyof T, keyof U>]?: never };