"""Generate GraphQL queries for API Key operations."""

from typing import List


class ApiKeysQueryGenerator:
    """Generate API Key related GraphQL queries."""
    
    def generate(self) -> List[str]:
        """Generate all API Key queries and mutations."""
        queries = []
        
        # Add comment
        queries.append("# API Key Queries")
        
        # GetApiKeys query
        queries.append("""query GetApiKeys($service: String) {
  api_keys(service: $service) {
    id
    label
    service
    key
  }
}""")
        
        # GetApiKey query
        queries.append("""query GetApiKey($id: ID!) {
  api_key(id: $id) {
    id
    label
    service
  }
}""")
        
        # GetAvailableModels query
        queries.append("""query GetAvailableModels($service: String!, $apiKeyId: ID!) {
  available_models(service: $service, api_key_id: $apiKeyId)
}""")
        
        # Add comment
        queries.append("# API Key Mutations")
        
        # CreateApiKey mutation
        queries.append("""mutation CreateApiKey($input: CreateApiKeyInput!) {
  create_api_key(input: $input) {
    success
    api_key {
      id
      label
      service
    }
    message
    error
  }
}""")
        
        # TestApiKey mutation
        queries.append("""mutation TestApiKey($id: ID!) {
  test_api_key(id: $id) {
    success
    message
    error
  }
}""")
        
        # DeleteApiKey mutation
        queries.append("""mutation DeleteApiKey($id: ID!) {
  delete_api_key(id: $id) {
    success
    message
  }
}""")
        
        return queries