import React, { useState, useEffect } from 'react';
import { Button, Input, Modal, Select, SelectItem } from '@/shared/components';
import { ApiKey, createErrorHandlerFactory } from '@/shared/types';
import { useConsolidatedDiagramStore } from '@/shared/stores';
import { Trash2, Plus, Eye, EyeOff } from 'lucide-react';
import { API_ENDPOINTS, getApiUrl } from '@/shared/utils/apiConfig';
import { toast } from 'sonner';

interface ApiKeysModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const API_SERVICES = [
  { value: 'claude', label: 'Claude (Anthropic)' },
  { value: 'openai', label: 'ChatGPT (OpenAI)' },
  { value: 'grok', label: 'Grok' },
  { value: 'gemini', label: 'Gemini (Google)' },
  { value: 'custom', label: 'Custom' },
] as const;

const ApiKeysModal: React.FC<ApiKeysModalProps> = ({ isOpen, onClose }) => {
  const { apiKeys, addApiKey, deleteApiKey, loadApiKeys } = useConsolidatedDiagramStore();
  const [newKeyForm, setNewKeyForm] = useState<Partial<ApiKey>>({
    name: '',
    service: 'claude',
    keyReference: '',
  });
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  // Create error handler for API key operations
  const createErrorHandler = createErrorHandlerFactory(toast);

  // Load API keys when modal opens
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      loadApiKeys()
        .catch((error) => {
          console.error('Failed to load API keys:', error);
          setErrors({ general: 'Failed to load existing API keys' });
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, loadApiKeys]);

  const handleAddKey = async () => {
    setErrors({});
    
    if (!newKeyForm.name?.trim()) {
      setErrors({ name: 'Name is required' });
      return;
    }
    
    if (!newKeyForm.keyReference?.trim()) {
      setErrors({ keyReference: 'API key is required' });
      return;
    }

    try {
      // Call backend API to create API key
      const response = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newKeyForm.name.trim(),
          service: newKeyForm.service || 'claude',
          key: newKeyForm.keyReference.trim()
        })
      });

      if (!response.ok) {
        const error = await response.json();
        setErrors({ keyReference: error.error || 'Failed to create API key' });
        return;
      }

      const result = await response.json();
      
      // Add to local store with backend ID
      const newKey: ApiKey = {
        id: result.id,
        name: result.name || newKeyForm.name.trim(),
        service: result.service || newKeyForm.service || 'claude',
        keyReference: '***hidden***', // Don't store raw key in frontend
      };

      addApiKey(newKey);
      
      // Reload API keys to ensure everything is in sync
      await loadApiKeys();
      
      // Reset form
      setNewKeyForm({
        name: '',
        service: 'claude',
        keyReference: '',
      });
      
      toast.success(`API key "${newKey.name}" added successfully`);
    } catch (error) {
      setErrors({ keyReference: 'Network error: Failed to create API key' });
    }
  };

  const handleDeleteKey = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this API key?')) {
      try {
        // Call backend API to delete
        const response = await fetch(getApiUrl(API_ENDPOINTS.API_KEY_BY_ID(id)), {
          method: 'DELETE'
        });

        if (!response.ok) {
          throw new Error('Failed to delete API key');
        }

        // Remove from local store
        deleteApiKey(id);
      } catch (error) {
        const errorHandler = createErrorHandler('Delete API Key');
        errorHandler(error as Error);
      }
    }
  };

  const toggleShowKey = (id: string) => {
    setShowKeys(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const maskApiKey = (key: string) => {
    if (!key) return '';
    const visibleChars = 4;
    if (key.length <= visibleChars * 2) return '••••••••';
    return `${key.slice(0, visibleChars)}••••••••${key.slice(-visibleChars)}`;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="API Keys" className="max-w-2xl">
      <div className="space-y-6">
        {/* Existing API Keys */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Configured API Keys
          </h3>
          {apiKeys.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              No API keys configured yet. Add one below.
            </p>
          ) : (
            <div className="space-y-2">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{key.name}</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        ({API_SERVICES.find(s => s.value === key.service)?.label})
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="text-xs font-mono text-gray-600 dark:text-gray-400">
                        {showKeys[key.id] ? key.keyReference : maskApiKey(key.keyReference || '')}
                      </code>
                      <button
                        onClick={() => toggleShowKey(key.id)}
                        className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                      >
                        {showKeys[key.id] ? (
                          <EyeOff className="w-3 h-3 text-gray-500" />
                        ) : (
                          <Eye className="w-3 h-3 text-gray-500" />
                        )}
                      </button>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteKey(key.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add New Key Form */}
        <div className="border-t pt-6">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Add New API Key
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Name
              </label>
              <Input
                placeholder="e.g., Production Claude Key"
                value={newKeyForm.name || ''}
                onChange={(e) => setNewKeyForm({ ...newKeyForm, name: e.target.value })}
                className={errors.name ? 'border-red-500' : ''}
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Service
              </label>
              <Select
                value={newKeyForm.service || 'claude'}
                onValueChange={(value) => setNewKeyForm({ ...newKeyForm, service: value as ApiKey['service'] })}
              >
                {API_SERVICES.map((service) => (
                  <SelectItem key={service.value} value={service.value}>
                    {service.label}
                  </SelectItem>
                ))}
              </Select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Key
              </label>
              <Input
                type="password"
                placeholder="sk-..."
                value={newKeyForm.keyReference || ''}
                onChange={(e) => setNewKeyForm({ ...newKeyForm, keyReference: e.target.value })}
                className={errors.keyReference ? 'border-red-500' : ''}
              />
              {errors.keyReference && <p className="text-red-500 text-sm mt-1">{errors.keyReference}</p>}
            </div>
            
            <Button
              onClick={handleAddKey}
              className="w-full"
              disabled={!newKeyForm.name || !newKeyForm.keyReference}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add API Key
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default ApiKeysModal;