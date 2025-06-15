/**
 * useApiKeyOperations - API Key management hook
 * 
 * This hook provides operations for managing API keys in the store.
 * Built using the store operation factory for consistency.
 */

import { createStoreOperationHook } from './factories';
import { apiKeyId, type DomainApiKey, type ApiService } from '@/types';

// Create the hook using our factory
export const useApiKeyOperations = createStoreOperationHook<DomainApiKey, [string, ApiService]>({
  entityName: 'API Key',
  entityNamePlural: 'API Keys',
  
  // Store selectors
  selectCollection: (state) => state.apiKeys,
  selectAddAction: (state) => state.addApiKey,
  selectUpdateAction: (state) => (id: string, updates: Partial<DomainApiKey>) => 
    state.updateApiKey(apiKeyId(id), updates),
  selectDeleteAction: (state) => (id: string) => 
    state.deleteApiKey(apiKeyId(id)),
  selectClearAction: (state) => state.closeApiKeysModal,
  
  // Validation
  validateAdd: (name: string, service: ApiService) => {
    const errors: string[] = [];
    
    if (!name || name.trim().length === 0) {
      errors.push('API key name is required');
    }
    
    if (!service) {
      errors.push('Service type is required');
    }
    
    // Validate service is a valid API service
    const validServices: ApiService[] = ['openai', 'gemini', 'claude', 'grok'];
    if (!validServices.includes(service)) {
      errors.push(`Invalid service: ${service}`);
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },
  
  validateUpdate: (_id: string, updates: Partial<DomainApiKey>) => {
    const errors: string[] = [];
    
    if (updates.label !== undefined && (!updates.label || updates.label.trim().length === 0)) {
      errors.push('API key name cannot be empty');
    }
    
    if (updates.service !== undefined) {
      const validServices: ApiService[] = ['openai', 'gemini', 'claude', 'grok'];
      if (!validServices.includes(updates.service)) {
        errors.push(`Invalid service: ${updates.service}`);
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },
  
  // Lifecycle hooks
  beforeAdd: (name: string, service: ApiService) => {
    // Trim the name before adding
    return [name.trim(), service];
  },
  
  afterAdd: async (_id: string, name: string, service: ApiService) => {
    // Log API key addition for debugging
    console.log(`Added API key: ${name} for service: ${service}`);
  },
  
  beforeDelete: async (_id: string) => {
    // Could check if API key is in use by any persons
    // For now, always allow deletion
    return true;
  },
  
  // Custom messages
  messages: {
    addSuccess: (name: string, service: ApiService) => `Added API key "${name}" for ${service}`,
    updateSuccess: () => `Updated API key`,
    deleteSuccess: () => `Removed API key`,
    addError: 'Failed to add API key',
    updateError: 'Failed to update API key',
    deleteError: 'Failed to remove API key'
  },
  
  // Options
  options: {
    useTransaction: true,
    showToasts: true,
    trackDirty: true
  }
});

// Export additional utilities specific to API keys
export const useApiKeyUtils = () => {
  const { items, getById } = useApiKeyOperations();
  
  // Get API keys by service
  const getByService = (service: ApiService): DomainApiKey[] => {
    return items.filter((key: DomainApiKey) => key.service === service);
  };
  
  // Check if a service has any API keys
  const hasKeysForService = (service: ApiService): boolean => {
    return items.some((key: DomainApiKey) => key.service === service);
  };
  
  // Get the first available key for a service
  const getFirstKeyForService = (service: ApiService): DomainApiKey | undefined => {
    return items.find((key: DomainApiKey) => key.service === service);
  };
  
  // Find API key by label
  const getByLabel = (name: string): DomainApiKey | undefined => {
    return items.find((key: DomainApiKey) => key.label === name);
  };
  
  return {
    getByService,
    hasKeysForService,
    getFirstKeyForService,
    getByLabel,
    getApiKeyById: getById
  };
};