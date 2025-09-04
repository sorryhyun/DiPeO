// FILE: src/core/di.ts

import type { User } from '@/core/contracts'

// Lightweight DI container for runtime registration and resolution of services.
// This file is intentionally self-contained and avoids runtime side effects.

/**
 * Token type used to strongly-type DI registrations.
 * Each token carries a phantom type parameter for TS inference.
 */
export type Token<T> = symbol & { __type?: T }

// Service shape definitions (local to DI container to avoid circular deps)
type ApiClientShape = {
  get<T>(path: string, opts?: any): Promise<T>
  post<T>(path: string, body?: any, opts?: any): Promise<T>
  put<T>(path: string, body?: any, opts?: any): Promise<T>
  delete<T>(path: string, opts?: any): Promise<T>
}

type AuthServiceShape = {
  login(payload: { email: string; password: string; otp?: string }): Promise<{ user: User; tokens: any }>
  logout(): Promise<void>
  refresh(): Promise<any>
  getCurrentUser(): Promise<User | null>
}

type StorageServiceShape = {
  get<T>(key: string): T | null
  set<T>(key: string, value: T): void
  remove(key: string): void
}

type WebSocketServiceShape = {
  connect(): Promise<void>
  disconnect(): Promise<void>
  send(event: string, payload?: any): void
  on(event: string, handler: (payload: any) => void): () => void
}

// EventBus type (imported for typing if available)
import type { EventBus } from '@/core/events'

// Tokens registry (typed)
export const TOKENS = {
  ApiClient: Symbol('ApiClient') as Token<ApiClientShape>,
  AuthService: Symbol('AuthService') as Token<AuthServiceShape>,
  StorageService: Symbol('StorageService') as Token<StorageServiceShape>,
  WebSocketService: Symbol('WebSocketService') as Token<WebSocketServiceShape>,
  EventBus: Symbol('EventBus') as Token<EventBus>,
} as const

// Internal container implementation
export class Container {
  private registry: Map<symbol, any> = new Map()
  private factories: Map<symbol, (c: Container) => any> = new Map()

  register<T>(token: Token<T>, value: T): void {
    const key = token as symbol
    this.registry.set(key, value)
  }

  registerFactory<T>(token: Token<T>, factory: (c: Container) => T): void {
    const key = token as symbol
    this.factories.set(key, factory)
  }

  resolve<T>(token: Token<T>): T {
    const key = token as symbol

    if (this.registry.has(key)) {
      return this.registry.get(key) as T
    }

    const factory = this.factories.get(key)
    if (factory) {
      const value = factory(this)
      // Cache the produced value for subsequent resolutions
      this.registry.set(key, value)
      this.factories.delete(key)
      return value as T
    }

    throw new Error(`DI: No registration found for token ${String(key)}`)
  }

  has(token: Token<any>): boolean {
    const key = token as symbol
    return this.registry.has(key) || this.factories.has(key)
  }

  reset(): void {
    this.registry.clear()
    this.factories.clear()
  }
}

// Public singleton container and helpers
export const container = new Container()
export const register = <T>(token: Token<T>, value: T): void => container.register(token, value)
export const resolve = <T>(token: Token<T>): T => container.resolve(token)

// Optional: expose a tiny API for tests/examples
export default Container

// Self-check comments
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)