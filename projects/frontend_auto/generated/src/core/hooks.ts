// FILE: src/core/hooks.ts

import type { AppConfig } from '@/app/config'
import type { EventBus } from '@/core/events'
import type { Container } from '@/core/di'

export type HookPoint =
  | 'beforeApiRequest'
  | 'afterApiResponse'
  | 'onLogin'
  | 'onLogout'
  | 'onRouteChange'
  | 'onAppBoot'

export interface HookContext {
  appConfig: AppConfig
  eventBus: EventBus
  diContainer: Container
}

// Generic hook function type: allow sync or async handlers
export type HookFn<TArgs extends any[] = any[], TRet = void> = (
  context: HookContext,
  ...args: TArgs
) => TRet | Promise<TRet>

class HookRegistry {
  private hooks: Record<HookPoint, Array<{ fn: HookFn<any, any>; priority: number }>> = {
    beforeApiRequest: [],
    afterApiResponse: [],
    onLogin: [],
    onLogout: [],
    onRouteChange: [],
    onAppBoot: []
  }

  register<P extends HookPoint>(
    point: P,
    fn: HookFn<any, any>,
    priority: number = 100
  ): () => void {
    const list = this.hooks[point] ?? []
    const entry = { fn, priority }
    list.push(entry)
    // keep deterministic order
    list.sort((a, b) => a.priority - b.priority)
    this.hooks[point] = list

    // return unregister function
    return () => {
      const arr = this.hooks[point] ?? []
      this.hooks[point] = arr.filter((h) => h.fn !== fn)
    }
  }

  list<P extends HookPoint>(point: P): Array<{ fn: HookFn<any, any>; priority: number }> {
    const arr = this.hooks[point] ?? []
    return arr.slice()
  }

  async run<P extends HookPoint, TArgs extends any[]>(point: P, context: HookContext, ...args: TArgs): Promise<void> {
    const items = this.hooks[point] ?? []
    // Execute in priority order; catch errors to avoid blocking other hooks
    for (const h of items) {
      try {
        await h.fn(context, ...args)
      } catch (err) {
        try {
          // best-effort logging if console available
          // eslint-disable-next-line no-console
          console.error('[HookRegistry] error in hook', point, err)
        } catch {
          // swallow
        }
      }
    }
  }
}

const _registry = new HookRegistry()

export function registerHook<P extends HookPoint>(
  point: P,
  fn: HookFn<any, any>,
  priority?: number
): () => void {
  return _registry.register(point, fn, priority)
}

export function useHook<P extends HookPoint>(
  point: P,
  fn: HookFn<any, any>,
  priority?: number
): () => void {
  // Lightweight React-aware helper: register immediately and return unregister()
  // Consumers may wrap this inside React.useEffect if needed; this is intentionally lightweight.
  return _registry.register(point, fn, priority)
}

export function runHooks<P extends HookPoint, TArgs extends any[]>(
  point: P,
  context: HookContext,
  ...args: TArgs
): Promise<void> {
  return _registry.run(point, context, ...args)
}

export { HookRegistry }

// Self-check comments (app-wide governance)
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)