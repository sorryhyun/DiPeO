/**
 * Feature flags configuration
 */

/**
 * Check if GraphQL should be used instead of REST API
 * Can be controlled via:
 * 1. Environment variable: VITE_USE_GRAPHQL=true
 * 2. URL parameter: ?useGraphQL=true
 */
export function shouldUseGraphQL(): boolean {
  // Check environment variable
  if (import.meta.env.VITE_USE_GRAPHQL === 'true') {
    return true;
  }
  
  // Check URL parameter
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('useGraphQL') === 'true') {
      return true;
    }
  }
  
  // Default to false for now (will change to true after migration)
  return false;
}