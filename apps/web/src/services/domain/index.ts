/**
 * Domain services export
 * Contains all business logic services
 */

export { DiagramService } from './diagram';
export { ExecutionService } from './execution';
export { ValidationService } from './validation';
export { NodeFactory } from './node-factory';
export { PersonService } from './person';

// Migrated services from core/services
export { DiagramOperations } from './diagram-operations';
export { NodeService } from './node-service';
export { ValidationService as CoreValidationService } from './validation-service';

// Type exports
export type * from './validation';