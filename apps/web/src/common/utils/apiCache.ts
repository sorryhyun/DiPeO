// API cache utility - placeholder for now
export class ApiCache {
  get(key: string) { return null; }
  set(key: string, value: any) {}
  clear() {}
}

export const apiCache = new ApiCache();