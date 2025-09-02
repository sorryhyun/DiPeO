// FILE: src/core/hooks.ts

import type { AppConfig } from '@/app/config'
import { appConfig } from '@/app/config'
import type { EventBus } from '@/core/events'
import { eventBus } from '@/core/events'
import type { Container } from '@/core/di'
import { container as diContainerInstance } from '@/core/di'

export type HookPoint =
  | 'beforeApiRequest'
  | 'afterApiResponse'
  | 'onLogin'
  | 'onLogout'
  | 'onRouteChange'
  | 'onAppBoot'

export interface HookContext {
  appConfig: AppConfig
  eventBus: EventBus<any>
  diContainer: Container
}

export type HookFn<TArgs extends any[] = any[], TRet = void> = (
  context: HookContext,
  ...args: TArgs
) => TRet | Promise<TRet>

export class HookRegistry {
  private registry = new Map<string, Array<{ fn: HookFn<any, any>; priority: number }>>()

  register<P extends HookPoint>(point: P, fn: HookFn<any, any>, priority: number = 100): () => void {
    const key = point as string
    const bucket = this.registry.get(key) ?? []
    const item = { fn, priority }
    bucket.push(item)
    bucket.sort((a, b) => a.priority - b.priority)
    this.registry.set(key, bucket)

    let active = true
    return () => {
      if (!active) return
      active = false
      const arr = this.registry.get(key)
      if (!arr) return
      const idx = arr.indexOf(item)
      if (idx >= 0) arr.splice(idx, 1)
    }
  }

  list<P extends HookPoint>(point: P): Array<{ fn: HookFn<any, any>; priority: number }> {
    const arr = this.registry.get(point as string) ?? []
    return arr.slice().sort((a, b) => a.priority - b.priority)
  }

  async run<P extends HookPoint, TArgs extends any[]>(point: P, ...args: TArgs): Promise<void> {
    const items = this.list(point)
    const ctx = this.makeContext()
    for (const { fn } of items) {
      try {
        const res = (fn as any)(ctx, ...args)
        if (res && typeof (res as any).then === 'function') {
          await (res as Promise<any>)
        }
      } catch (err) {
        debugLog('Hook run error', point, err)
      }
    }
  }

  private makeContext(): HookContext {
    return {
      appConfig,
      eventBus,
      diContainer: diContainerInstance as unknown as Container
    }
  }
}

// Singleton registry instance
export const hookRegistry = new HookRegistry()

// Convenience API
export function registerHook<P extends HookPoint>(point: P, fn: HookFn<any>, priority: number = 100): () => void {
  return hookRegistry.register(point, fn, priority)
}

export function runHooks<P extends HookPoint, TArgs extends any[]>(point: P, ...args: TArgs): Promise<void> {
  return hookRegistry.run(point, ...args)
}

// Lightweight React-aware wrapper (no-op unless consumed by a React-aware consumer)
export function useHook<P extends HookPoint, TArgs extends any[]>(
  point: P,
  fn: HookFn<any, any>,
  priority: number = 100
): void {
  // In non-React environments, simply register the hook.
  // If used inside a React component, consumer can replace with a proper useEffect-based wrapper.
  registerHook(point, fn, priority)
}

// Self-Check comments
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)