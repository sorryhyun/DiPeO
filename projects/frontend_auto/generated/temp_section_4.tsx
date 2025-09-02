// FILE: src/core/hooks.ts
import type { User, Patient, Appointment, ApiResult } from '@/core/contracts'
import { eventBus } from '@/core/events'
import { container } from '@/core/di'
import { config } from '@/app/config'
import type { AppConfig } from '@/app/config'
import { useEffect } from 'react'

// Section-local: Hook points used across the app
export type HookPoint =
  | 'beforeApiRequest'
  | 'afterApiResponse'
  | 'onLogin'
  | 'onLogout'
  | 'onRouteChange'
  | 'onAppBoot'

// Context passed to hook functions
export interface HookContext {
  appConfig: AppConfig
  eventBus: typeof eventBus
  diContainer: typeof container
}

// Hook function signature
export type HookFn<TArgs extends any[] = any[], TRet = void> = (
  context: HookContext,
  ...args: TArgs
) => TRet | Promise<TRet>

// Internal registry implementation
export class HookRegistry {
  private store = new Map<HookPoint, Array<{ fn: HookFn; priority: number }>>()

  register(point: HookPoint, fn: HookFn, priority = 100): () => void {
    const bucket = this.store.get(point) ?? []
    bucket.push({ fn, priority })
    this.store.set(point, bucket)

    // Unregister function
    return () => {
      const arr = this.store.get(point) ?? []
      const idx = arr.findIndex((entry) => entry.fn === fn)
      if (idx >= 0) {
        arr.splice(idx, 1)
      }
      this.store.set(point, arr)
    }
  }

  list(point: HookPoint): Array<{ fn: HookFn; priority: number }> {
    const bucket = this.store.get(point) ?? []
    // Return a shallow copy sorted by priority (ascending)
    return [...bucket].sort((a, b) => a.priority - b.priority)
  }

  async run(point: HookPoint, ...args: any[]): Promise<void> {
    const list = this.list(point)
    const ctx: HookContext = {
      appConfig: config as AppConfig,
      eventBus,
      diContainer: container
    }

    for (const { fn } of list) {
      try {
        const result = fn(ctx, ...args)
        if (result && typeof (result as any).then === 'function') {
          await (result as Promise<any>)
        }
      } catch (err) {
        // Swallow errors to allow other hooks to proceed; log for visibility
        // eslint-disable-next-line no-console
        console.error('[core/hooks] error in hook', point, err)
      }
    }
  }
}

// Singleton instance
export const hooks = new HookRegistry()

// API surface
export function registerHook<P extends HookPoint>(
  point: P,
  fn: HookFn,
  priority = 100
): () => void {
  return hooks.register(point, fn, priority)
}

// React-friendly hook wrapper (to be used inside React components)
export function useHook<P extends HookPoint>(point: P, fn: HookFn, priority = 100) {
  useEffect(() => {
    const unregister = hooks.register(point, fn, priority)
    return () => unregister()
  }, [point, fn, priority])
}

// Default export for compatibility in some tooling
export default { hooks }

// Self-check comments (for tooling visibility)
//
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)