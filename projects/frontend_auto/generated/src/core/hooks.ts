// FILE: src/core/hooks.ts

import { appConfig } from '@/app/config'
import { eventBus } from '@/core/events'
import { container } from '@/core/di'
import React, { useEffect } from 'react'

// section-local helpers and types

export type HookPoint =
  | 'beforeApiRequest'
  | 'afterApiResponse'
  | 'onLogin'
  | 'onLogout'
  | 'onRouteChange'
  | 'onAppBoot'

// Lightweight HookContext
export interface HookContext {
  appConfig: typeof appConfig
  eventBus: typeof eventBus
  diContainer: typeof container
}

// Generic hook function signature
export type HookFn<TArgs extends any[] = any[], TRet = void> = (
  context: HookContext,
  ...args: TArgs
) => TRet | Promise<TRet>

class HookRegistry {
  private hooks = new Map<HookPoint, Array<{ fn: HookFn<any[], any>; priority: number }>>()

  register<P extends HookPoint>(point: P, fn: HookFn<any[], any>, priority = 100): () => void {
    const list = this.hooks.get(point) ?? []
    const entry = { fn, priority }
    list.push(entry)
    // maintain ascending priority
    list.sort((a, b) => a.priority - b.priority)
    this.hooks.set(point, list)

    // return unregister function
    return () => {
      const arr = this.hooks.get(point)
      if (!arr) return
      const idx = arr.findIndex((e) => e.fn === fn && e.priority === priority)
      if (idx >= 0) arr.splice(idx, 1)
      if (arr.length === 0) this.hooks.delete(point)
    }
  }

  list<P extends HookPoint>(point: P): Array<{ fn: HookFn<any[], any>; priority: number }> {
    const arr = this.hooks.get(point) ?? []
    return arr.map((h) => ({ fn: h.fn, priority: h.priority }))
  }

  async run<P extends HookPoint, TArgs extends any[] = any[]>(point: P, ...args: TArgs): Promise<void> {
    const ctx: HookContext = {
      appConfig,
      eventBus,
      diContainer: container,
    } as any

    const snapshot = this.list(point).slice().sort((a, b) => a.priority - b.priority)

    for (const { fn } of snapshot) {
      try {
        const result = (fn as any)(ctx, ...args)
        if (result && typeof (result as any).then === 'function') {
          await (result as Promise<any>)
        }
      } catch (err) {
        try {
          // eslint-disable-next-line no-console
          console.error('[Hooks] error in hook', point, err)
        } catch {
          // ignore
        }
      }
    }
  }

  clear(): void {
    this.hooks.clear()
  }
}

// Singleton registry instance
const hookRegistry = new HookRegistry()

// Public API

export function registerHook<P extends HookPoint>(
  point: P,
  fn: HookFn<any[], any>,
  priority?: number
): () => void {
  return hookRegistry.register(point, fn, priority ?? 100)
}

export function runHooks<P extends HookPoint, TArgs extends any[] = any[]>(point: P, ...args: TArgs): Promise<void> {
  return hookRegistry.run(point, ...args)
}

// React-friendly hook wrapper
export function useHook<P extends HookPoint, TArgs extends any[] = any[]>(
  point: P,
  fn: HookFn<TArgs, any>,
  priority?: number
): void {
  useEffect(() => {
    // register on mount, unregister on unmount
    const unregister = hookRegistry.register(point, fn as any, priority ?? 100)
    return () => unregister()
  }, [point, priority])
}

export { HookRegistry }

// Self-Check
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)