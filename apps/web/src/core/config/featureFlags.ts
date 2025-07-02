// 1. Environment variable: VITE_USE_GRAPHQL=true
// 2. URL parameter: ?useGraphQL=true

export function shouldUseGraphQL(): boolean {
  if (import.meta.env.VITE_USE_GRAPHQL === 'true') {
    return true;
  }
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('useGraphQL') === 'true') {
      return true;
    }
  }

  // Default to false
  return false;
}