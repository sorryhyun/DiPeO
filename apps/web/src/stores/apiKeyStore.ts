import { createWithEqualityFn } from 'zustand/traditional';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { entityIdGenerators } from '@/utils/id';
import { DomainApiKey } from '@/types';
import { api } from '@/utils';

export interface ApiKeyState {
  apiKeys: DomainApiKey[];
  
  addApiKey: (apiKey: Omit<DomainApiKey, 'id'>) => void;
  updateApiKey: (apiKeyId: string, apiKeyData: Partial<DomainApiKey>) => void;
  deleteApiKey: (apiKeyId: string) => void;
  getApiKeyById: (apiKeyId: string) => DomainApiKey | undefined;
  clearApiKeys: () => void;
  loadApiKeys: () => Promise<void>;
  setApiKeys: (apiKeys: DomainApiKey[]) => void;
}

export const useApiKeyStore = createWithEqualityFn<ApiKeyState>()(
  devtools(
    subscribeWithSelector(
      (set, get) => ({
        apiKeys: [],
        
        addApiKey: (apiKeyData: Omit<DomainApiKey, 'id'>) => {
          const newApiKey = {
            ...apiKeyData,
            id: entityIdGenerators.apiKey()
          } as DomainApiKey;
          set(state => ({ apiKeys: [...state.apiKeys, newApiKey] }));
        },
        
        updateApiKey: (id: string, data: Partial<DomainApiKey>) => {
          set(state => ({
            apiKeys: state.apiKeys.map(key => 
              key.id === id ? { ...key, ...data } : key
            )
          }));
        },
        
        deleteApiKey: (id: string) => {
          set(state => ({
            apiKeys: state.apiKeys.filter(key => key.id !== id)
          }));
        },
        
        getApiKeyById: (id: string) => {
          return get().apiKeys.find(key => key.id === id);
        },
        
        clearApiKeys: () => {
          set({ apiKeys: [] });
        },
        
        loadApiKeys: async () => {
          try {
            const data = await api.apiKeys.list();
            const apiKeys = data.map((key) => ({
              id: key.id,
              name: key.name,
              service: key.service as DomainApiKey['service']
            }));
            
            set({ apiKeys });
          } catch (error) {
            console.error('Error loading API keys:', error);
            throw error;
          }
        },
        
        setApiKeys: (apiKeys: DomainApiKey[]) => {
          set({ apiKeys });
        },
      })
    )
  )
);