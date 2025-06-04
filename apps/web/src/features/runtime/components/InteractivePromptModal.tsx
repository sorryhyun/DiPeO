/**
 * Interactive Prompt Modal - Displays prompts from PersonJob nodes and collects user responses
 */

import React, { useState, useEffect } from 'react';
import { Modal } from '@/common/components/Modal';
import { Button } from '@/common/components/Button';

export interface InteractivePromptData {
  nodeId: string;
  executionId: string;
  prompt: string;
  context?: {
    person_id?: string;
    person_name?: string;
    model?: string;
    service?: string;
    execution_count?: number;
  };
}

interface InteractivePromptModalProps {
  prompt: InteractivePromptData | null;
  onResponse: (nodeId: string, response: string) => void;
  onCancel?: () => void;
}

export const InteractivePromptModal: React.FC<InteractivePromptModalProps> = ({
  prompt,
  onResponse,
  onCancel
}) => {
  const [response, setResponse] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset response when new prompt appears
  useEffect(() => {
    if (prompt) {
      setResponse('');
      setIsSubmitting(false);
    }
  }, [prompt]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt || isSubmitting) return;

    setIsSubmitting(true);
    onResponse(prompt.nodeId, response);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit(e);
    }
  };

  if (!prompt) return null;

  const { context } = prompt;
  const personInfo = context?.person_name || context?.person_id || 'Person';
  const modelInfo = context?.model ? ` (${context.model})` : '';

  return (
    <Modal
      isOpen={true}
      onClose={() => onCancel?.()}
      title={`Interactive Prompt from ${personInfo}${modelInfo}`}
      className="max-w-2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Prompt:</h3>
          <div className="bg-gray-50 rounded-md p-3 text-sm text-gray-800 whitespace-pre-wrap">
            {prompt.prompt}
          </div>
        </div>

        <div>
          <label htmlFor="response" className="block text-sm font-medium text-gray-700 mb-2">
            Your Response:
          </label>
          <textarea
            id="response"
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            rows={4}
            placeholder="Type your response here..."
            autoFocus
            disabled={isSubmitting}
          />
          <p className="mt-1 text-xs text-gray-500">
            Press Ctrl+Enter to submit
          </p>
        </div>

        {context?.execution_count !== undefined && (
          <div className="text-xs text-gray-500">
            Iteration: {context.execution_count + 1}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={() => onCancel?.()}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="default"
            disabled={!response.trim() || isSubmitting}
          >
            {isSubmitting ? 'Sending...' : 'Send Response'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default InteractivePromptModal;