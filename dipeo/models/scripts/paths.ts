/**
 * Common path constants for all generation scripts
 * This centralizes path definitions to avoid relative path issues when scripts are moved
 */

import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

// Get the root directory of the models package
const __filename = fileURLToPath(import.meta.url);
const scriptsDir = dirname(__filename);
const modelsRoot = join(scriptsDir, '..');
const projectRoot = join(modelsRoot, '..', '..');

export const PATHS = {
  // Models package paths
  modelsRoot,
  tsConfig: join(modelsRoot, 'tsconfig.json'),
  srcDir: join(modelsRoot, 'src'),
  generatedDir: join(modelsRoot, '__generated__'),
  modelsOutput: join(modelsRoot, 'models.py'),
  
  // Frontend output paths
  webGeneratedDir: join(projectRoot, 'apps', 'web', 'src', '__generated__'),
  webDomainMappings: join(projectRoot, 'apps', 'web', 'src', '__generated__', 'domain', 'mappings.ts'),
  webNodesSchemas: join(projectRoot, 'apps', 'web', 'src', '__generated__', 'nodes', 'schemas.ts'),
  webNodesFields: join(projectRoot, 'apps', 'web', 'src', '__generated__', 'nodes', 'fields.ts'),
  webEntitiesDir: join(projectRoot, 'apps', 'web', 'src', '__generated__', 'entities'),
  
  // Backend output paths
  serverGraphQLDir: join(projectRoot, 'apps', 'server', 'src', 'dipeo_server', 'api', 'graphql'),
  serverMutationsDir: join(projectRoot, 'apps', 'server', 'src', 'dipeo_server', 'api', 'graphql', 'mutations'),
  serverQueriesDir: join(projectRoot, 'apps', 'server', 'src', 'dipeo_server', 'api', 'graphql', 'queries'),
  serverGeneratedMutationsDir: join(projectRoot, 'apps', 'server', 'src', 'dipeo_server', 'api', 'graphql', 'generated', 'mutations'),
  serverGeneratedQueriesDir: join(projectRoot, 'apps', 'server', 'src', 'dipeo_server', 'api', 'graphql', 'generated', 'queries'),
  serverGeneratedTypesDir: join(projectRoot, 'apps', 'server', 'src', 'dipeo_server', 'api', 'graphql', 'generated'),
  
  // Core output paths
  coreStaticNodes: join(projectRoot, 'dipeo', 'core', 'static', 'generated_nodes.py'),
} as const;

