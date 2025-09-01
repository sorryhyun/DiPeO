import type { Appointment } from '@/core/contracts'

type EventHandler<T> = (payload: T, meta?: { ts: string }) => void | Promise<void>

export interface EventMap {
  'analytics.track': { event: string; payload?: Record<string, any> }
  'user.login': { userId: string; tokens?: any }
  'user.logout': { userId?: string }
  'appointment.created': { appointmentId: string }
  'appointment.updated': { appointmentId: string; changes?: Partial<Appointment> }
  'labresult.completed': { labId: string }
  [key: string]: any
}

const isDevelopment = (typeof import.meta !== 'undefined' && ((import.meta.env as any).MODE === 'development')) || false

class EventBus<EM extends EventMap = EventMap> {
  private handlers = new Map<string, Set<EventHandler<any>>>()

  on<K extends keyof EM>(event: K, handler: EventHandler<EM[K]>): () => void {
    const key = event as string
    let set = this.handlers.get(key)
    if (!set) {
      set = new Set<EventHandler<any>>()
      this.handlers.set(key, set)
    }
    set.add(handler as EventHandler<any>)
    return () => {
      set?.delete(handler as EventHandler<any>)
    }
  }

  off<K extends keyof EM>(event: K, handler?: EventHandler<EM[K]>): void {
    const key = event as string
    const set = this.handlers.get(key)
    if (!set) return
    if (handler) {
      set.delete(handler as EventHandler<any>)
    } else {
      set.clear()
    }
  }

  async emit<K extends keyof EM>(event: K, payload: EM[K], options?: { async?: boolean }): Promise<void> | void {
    const key = event as string
    const handlers = this.handlers.get(key)
    if (!handlers || handlers.size === 0) return

    const ts = new Date().toISOString()
    const meta = { ts }

    if (options?.async) {
      ;(async () => {
        for (const h of Array.from(handlers)) {
          try {
            await (h as EventHandler<EM[K]>)(payload, meta)
          } catch (e) {
            if (isDevelopment) {
              // eslint-disable-next-line no-console
              console.error('[EventBus] Async handler error', e)
            }
          }
        }
      })()
      return
    } else {
      for (const h of Array.from(handlers)) {
        try {
          const r = (h as EventHandler<EM[K]>) (payload, meta)
          if (r && typeof (r as any).then === 'function') {
            ;(r as Promise<any>).catch(() => {})
          }
        } catch (e) {
          if (isDevelopment) {
            // eslint-disable-next-line no-console
            console.error('[EventBus] Handler error', e)
          }
        }
      }
    }
  }

  clear(): void {
    this.handlers.clear()
  }
}

export function createEventBus<EM extends EventMap = EventMap>(): EventBus<EM> {
  return new EventBus<EM>()
}

export const eventBus = createEventBus<EventMap>()

export const on = <K extends keyof EventMap>(event: K, handler: EventMap[K] extends any ? EventHandler<EventMap[K]> : EventHandler<any>) =>
  (eventBus as any).on(event, handler)

export const off = <K extends keyof EventMap>(
  event: K,
  handler?: EventMap[K] extends any ? EventHandler<EventMap[K]> : EventHandler<any>
) => (eventBus as any).off(event, handler)

export const emit = <K extends keyof EventMap>(
  event: K,
  payload: EventMap[K],
  options?: { async?: boolean }
) => (eventBus as any).emit(event, payload, options)

/*
// Self-check comments
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)
*/