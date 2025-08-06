/**
 * Centralized services export
 * Phase 4 of frontend refactoring - Service Layer
 * 
 * This module provides a unified interface to all business services,
 * following clean architecture principles with clear separation of concerns.
 */

// API Services - External integrations (GraphQL only)
export { GraphQLService } from './api/graphql';

// Domain Services - Business logic
export { 
  DiagramService,
  ExecutionService,
  ValidationService,
  NodeFactory,
  PersonService,
  DiagramOperations,
  NodeService,
  CoreValidationService,
} from './domain';

// Conversion Services - Type transformations
export { 
  Converters,
  NodeConverter,
  ArrowConverter,
  HandleConverter,
  DiagramConverter,
  ExecutionConverter,
  PersonConverter,
} from './conversion';

// Re-export types
export type { ValidationResult, ValidationError, ValidationWarning } from './domain/validation';

/**
 * Unified Services facade
 * Provides a single entry point for all service operations
 * Uses lazy loading for code splitting
 */
export const Services = {
  // API layer (GraphQL only)
  api: {
    graphql: () => import('./api/graphql').then(m => m.GraphQLService),
  },
  
  // Domain layer - Business logic
  domain: {
    diagram: () => import('./domain/diagram').then(m => m.DiagramService),
    execution: () => import('./domain/execution').then(m => m.ExecutionService),
    validation: () => import('./domain/validation').then(m => m.ValidationService),
    nodeFactory: () => import('./domain/node-factory').then(m => m.NodeFactory),
    person: () => import('./domain/person').then(m => m.PersonService),
    diagramOperations: () => import('./domain/diagram-operations').then(m => m.DiagramOperations),
    nodeService: () => import('./domain/node-service').then(m => m.NodeService),
  },
  
  // Conversion layer - Type transformations
  conversion: () => import('./conversion').then(m => m.Converters),
} as const;

/**
 * Service initialization
 * Sets up any required service configurations
 */
export async function initializeServices(): Promise<void> {
  console.log('[Services] Initializing service layer...');
  
  // Services are now consolidated under apps/web/src/services/
  // - api/: GraphQL operations (no REST)
  // - domain/: Business logic and operations
  // - conversion/: Type converters between GraphQL/Domain/Store
  
  console.log('[Services] Service layer initialized');
}