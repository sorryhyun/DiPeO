import { useMutation, useSubscription } from '@apollo/client';
import {
  ExecutionUpdatesDocument,
  NodeUpdatesDocument,
  InteractivePromptsDocument,
  ExecuteDiagramDocument,
  ControlExecutionDocument,
  SubmitInteractiveResponseDocument,
  ExecutionUpdatesSubscription,
  NodeUpdatesSubscription,
  InteractivePromptsSubscription,
} from '@/__generated__/graphql';

export interface UseExecutionGraphQLProps {
  executionId: string | null;
  skip?: boolean;
}

export function useExecutionGraphQL({ executionId, skip = false }: UseExecutionGraphQLProps) {
  // Mutations
  const [executeDiagramMutation] = useMutation(ExecuteDiagramDocument);
  const [controlExecutionMutation] = useMutation(ControlExecutionDocument);
  const [submitInteractiveResponseMutation] = useMutation(SubmitInteractiveResponseDocument);

  // Subscriptions
  const { data: executionData } = useSubscription<ExecutionUpdatesSubscription>(
    ExecutionUpdatesDocument,
    {
      variables: { executionId: executionId! },
      skip: skip || !executionId,
    }
  );

  const { data: nodeData } = useSubscription<NodeUpdatesSubscription>(
    NodeUpdatesDocument,
    {
      variables: { executionId: executionId! },
      skip: skip || !executionId,
    }
  );

  const { data: promptData } = useSubscription<InteractivePromptsSubscription>(
    InteractivePromptsDocument,
    {
      variables: { executionId: executionId! },
      skip: skip || !executionId,
    }
  );

  return {
    // Mutations
    executeDiagram: executeDiagramMutation,
    controlExecution: controlExecutionMutation,
    submitInteractiveResponse: submitInteractiveResponseMutation,
    
    // Subscription data
    executionUpdates: executionData?.executionUpdates,
    nodeUpdates: nodeData?.nodeUpdates,
    interactivePrompts: promptData?.interactivePrompts,
  };
}