import { lazy } from 'react';

// Lazy load all node components
export const StartNode = lazy(() => import('./StartNode'));
export const ConditionNode = lazy(() => import('./ConditionNode'));
export const JobNode = lazy(() => import('./JobNode'));
export const DBNode = lazy(() => import('./DBNode'));
export const EndpointNode = lazy(() => import('./EndpointNode'));
export const PersonJobNode = lazy(() => import('./PersonJobNode'));