// src/core/events.ts

import type { User, Patient, Appointment } from '@/core/contracts'

// EventMap: default events. Other modules can augment this interface using module augmentation.
export type EventMap = {
  // Analytics tracking events
  'analytics.track': { event: string; payload?: Record<string, any> }

  // User lifecycle
  'user.login': { userId: string; tokens?: any }
  'user.logout': { userId?: string }

  // Appointments
  'appointment.created': { appointmentId: string }
  'appointment.updated': { appointmentId: string; changes?: Partial<Appointment> }

  // Lab results
  'labresult.completed': { labId: string }

  // Extendable: modules can augment EventMap to introduce new events
}

// Event handler type
export type EventHandler<T> = (payload: T, meta?: { ts: string }) => void | Promise<void>

// Core EventBus implementation
class EventBus<EM extends Record<string, any> = EventMap> {
  private handlers = new Map<string, Set<EventHandler<any>>>()

  on<K extends keyof EM>(event: K, handler: EventHandler<EM[K]>): () => void {
    const key = String(event)
    let set = this.handlers.get(key)
    if (!set) {
      set = new Set<EventHandler<any>>()
      this.handlers.set(key, set)
    }
    set.add(handler as EventHandler<any>)
    // unsubscribe function
    return () => {
      const s = this.handlers.get(key)
      if (s) {
        s.delete(handler as EventHandler<any>)
        if (s.size === 0) this.handlers.delete(key)
      }
    }
  }

  off<K extends keyof EM>(event: K, handler?: EventHandler<EM[K]>): void {
    const key = String(event)
    const set = this.handlers.get(key)
    if (!set) return
    if (!handler) {
      this.handlers.delete(key)
      return
    }
    set.delete(handler as EventHandler<any>)
    if (set.size === 0) this.handlers.delete(key)
  }

  async emit<K extends keyof EM>(
    event: K,
    payload: EM[K],
    options?: { async?: boolean }
  ): Promise<void> {
    const key = String(event)
    const set = this.handlers.get(key)
    if (!set || set.size === 0) return

    const ts = new Date().toISOString()
    const meta = { ts }
    const handlers = Array.from(set.values()) as EventHandler<EM[K]>[]

    if (options?.async) {
      for (const h of handlers) {
        try {
          await h(payload, meta)
        } catch (err) {
          // Do not crash the emitter; log in development if possible
          // eslint-disable-next-line no-console
          console.error('[EventBus] async handler error', err)
        }
      }
    } else {
      for (const h of handlers) {
        try {
          // Allow sync work or quick async fire-and-forget
          void h(payload, meta)
        } catch (err) {
          // eslint-disable-next-line no-console
          console.error('[EventBus] handler error', err)
        }
      }
    }
  }

  clear(): void {
    this.handlers.clear()
  }
}

// Public singleton instance
export const eventBus = new EventBus<EventMap>()

// Convenience bindings
export const on = eventBus.on.bind(eventBus)
export const off = eventBus.off.bind(eventBus)
export const emit = eventBus.emit.bind(eventBus)

// Self-check comments
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)