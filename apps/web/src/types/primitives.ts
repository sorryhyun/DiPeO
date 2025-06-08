// types/primitives.ts - Basic type definitions and utilities

export interface Vec2 { x: number; y: number }

export type Dict<V = unknown> = Record<string, V>;
export type Nullable<T> = T | null;
export type DeepPartial<T> = { [K in keyof T]?: DeepPartial<T[K]> };