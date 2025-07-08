import React, { useState, useEffect } from 'react';
import { Button } from '@/shared/components/forms/buttons';
import { Input } from '@/shared/components/forms';
import { Modal } from '@/shared/components/feedback';
import { createErrorHandlerFactory, DomainApiKey } from '@/core/types';
import { useApiKeyOperations } from '@/shared/hooks';
import { Trash2, Plus, Eye, EyeOff } from 'lucide-react';

interface ApiKeysModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Helper function to get display name for known services
const getServiceDisplayName = (service: string): string => {
  const serviceNames: Record<string, string> = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    google: 'Google AI',
    gemini: 'Google Gemini',
    grok: 'Grok',
    notion: 'Notion',
    google_search: 'Google Search',
    slack: 'Slack',
    github: 'GitHub',
  };
  return serviceNames[service.toLowerCase()] || service;
};

const ApiKeysModal: React.FC<ApiKeysModalProps> = ({ isOpen, onClose }) => {
  // Use GraphQL operations for API key management
  const graphQLOperations = useApiKeyOperations();
  
  // Convert Map to array for display
  const apiKeysArray = graphQLOperations.apiKeys;
    
  const [newKeyForm, setNewKeyForm] = useState<{ label: string; service: string; key: string }>({
    label: '',
    service: '',
    key: '',
  });
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [_loading, setLoading] = useState(false);

  // Create error handler for API key operations
  const createErrorHandler = createErrorHandlerFactory('ApiKeysModal');

  // Load API keys when modal opens
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      // API keys are already in the unified store
      setLoading(false);
    }
  }, [isOpen]);

  const handleAddKey = async () => {
    setErrors({});
    
    if (!newKeyForm.label?.trim()) {
      setErrors({ label: 'Name is required' });
      return;
    }
    
    if (!newKeyForm.service?.trim()) {
      setErrors({ service: 'Service is required' });
      return;
    }
    
    if (!newKeyForm.key?.trim()) {
      setErrors({ key: 'API key is required' });
      return;
    }

    try {
      // Use GraphQL mutation
      await graphQLOperations.createApiKey(
        newKeyForm.label.trim(),
        newKeyForm.service!.trim(),
        newKeyForm.key.trim()
      );
      
      // Reset form
      setNewKeyForm({
        label: '',
        service: '',
        key: '',
      });
    } catch {
      setErrors({ keyReference: 'Network error: Failed to create API key' });
    }
  };

  const handleDeleteKey = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this API key?')) {
      try {
        // Use GraphQL mutation
        await graphQLOperations.deleteApiKey(id);
      } catch (error) {
        createErrorHandler(error);
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
          {apiKeysArray.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              No API keys configured yet. Add one below.
            </p>
          ) : (
            <div className="space-y-2">
              {apiKeysArray.map((key: DomainApiKey) => (
                <div
                  key={key.id}
                  className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{key.label}</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        ({getServiceDisplayName(key.service)})
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="text-xs font-mono text-gray-600 dark:text-gray-400">
                        {showKeys[key.id] ? '***hidden***' : maskApiKey('***hidden***')}
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
                value={newKeyForm.label || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewKeyForm({ ...newKeyForm, label: e.target.value })}
                className={errors.name ? 'border-red-500' : ''}
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Service
              </label>
              <Input
                placeholder="e.g., openai, anthropic, notion, google_search"
                value={newKeyForm.service || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewKeyForm({ ...newKeyForm, service: e.target.value.toLowerCase() })}
                className={errors.service ? 'border-red-500' : ''}
              />
              {errors.service && <p className="text-red-500 text-sm mt-1">{errors.service}</p>}
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Common: openai, anthropic, gemini, grok, notion, google_search
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Key
              </label>
              <Input
                type="password"
                placeholder="sk-..."
                value={newKeyForm.key || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewKeyForm({ ...newKeyForm, key: e.target.value })}
                className={errors.key ? 'border-red-500' : ''}
              />
              {errors.key && <p className="text-red-500 text-sm mt-1">{errors.key}</p>}
            </div>
            
            <Button
              onClick={handleAddKey}
              className="w-full"
              disabled={!newKeyForm.label || !newKeyForm.key || graphQLOperations?.creatingApiKey}
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