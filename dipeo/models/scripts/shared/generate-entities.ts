/**
 * Entity Code Generation Orchestrator - Fixed Version
 * Coordinates the generation of GraphQL resolvers, React hooks, and types from entity definitions
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { glob } from 'glob';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { generateMutations, generateQueries, generateTypeAdditions } from '../backend/generate-graphql-resolvers';
import { generateHooks, generateGraphQLDocuments } from '../frontend/generate-react-hooks';
import { generateEntityInterfaces } from './generate-entity-interfaces';
import { EntityDefinition } from '../../src/entity-config';
import { PATHS } from '../paths';

const OUTPUT_PATHS = {
  serverMutations: PATHS.serverGeneratedMutationsDir,
  serverQueries: PATHS.serverGeneratedQueriesDir,
  serverTypes: PATHS.serverGeneratedTypesDir,
  hooks: path.join(PATHS.webGeneratedDir, 'entities'),
  graphql: path.join(PATHS.webGeneratedDir, 'entities'),
};

/**
 * Load all entity definitions
 */
async function loadEntityDefinitions(): Promise<EntityDefinition[]> {
  const quiet = process.env.QUIET === 'true';
  const entityFiles = await glob('entities/*.entity.ts', {
    cwd: PATHS.srcDir,
    absolute: false
  });
  
  const entities: EntityDefinition[] = [];
  
  for (const file of entityFiles) {
    if (!quiet) {
      console.log(`Loading entity from ${file}...`);
    }
    try {
      // Dynamic import of entity definition
      const module = await import(path.join(PATHS.srcDir, file));
      
      // Find the exported entity definition
      const entityExport = Object.values(module).find(
        (exp: any) => exp && typeof exp === 'object' && 'name' in exp && 'fields' in exp
      );
      
      if (entityExport) {
        entities.push(entityExport as EntityDefinition);
      } else {
        console.warn(`No entity definition found in ${file}`);
      }
    } catch (error) {
      console.error(`Failed to load entity from ${file}:`, error);
    }
  }
  
  return entities;
}

/**
 * Ensure directory exists
 */
async function ensureDir(dir: string): Promise<void> {
  try {
    await fs.mkdir(dir, { recursive: true });
  } catch (error) {
    // Directory might already exist
  }
}

/**
 * Write generated file with header
 */
async function writeGeneratedFile(filePath: string, content: string): Promise<void> {
  const quiet = process.env.QUIET === 'true';
  await ensureDir(path.dirname(filePath));
  await fs.writeFile(filePath, content, 'utf-8');
  if (!quiet) {
    console.log(`✅ Generated: ${path.relative(process.cwd(), filePath)}`);
  }
}

/**
 * Generate all code for a single entity
 */
async function generateEntityCode(entity: EntityDefinition): Promise<void> {
  const quiet = process.env.QUIET === 'true';
  if (!quiet) {
    console.log(`\n🔧 Generating code for ${entity.name}...`);
  }
  
  try {
    // 1. Generate GraphQL mutations (Python)
    const mutations = await generateMutations(entity);
    await writeGeneratedFile(
      path.join(OUTPUT_PATHS.serverMutations, `${entity.name.toLowerCase()}_mutation.py`),
      mutations
    );
    
    // 2. Generate query methods to be added to Query class
    const queryMethods = await generateQueryMethods(entity);
    if (queryMethods) {
      await writeGeneratedFile(
        path.join(OUTPUT_PATHS.serverQueries, `${entity.name.toLowerCase()}_queries.py`),
        queryMethods
      );
    }
    
    // 3. Generate React hooks
    const hooks = await generateHooks(entity);
    const hooksPath = path.join(OUTPUT_PATHS.hooks, 'hooks', `use${entity.name}Operations.ts`);
    await writeGeneratedFile(hooksPath, hooks);
    
    // 4. Generate GraphQL documents
    const documents = await generateGraphQLDocuments(entity);
    const graphqlPath = path.join(OUTPUT_PATHS.graphql, 'graphql', `${entity.name.toLowerCase()}.graphql`);
    await writeGeneratedFile(graphqlPath, documents);
    
    if (!quiet) {
      console.log(`✨ Successfully generated all code for ${entity.name}`);
    }
    
  } catch (error) {
    console.error(`❌ Failed to generate code for ${entity.name}:`, error);
    throw error;
  }
}

/**
 * Generate query methods for an entity (to be integrated into main Query class)
 */
async function generateQueryMethods(entity: EntityDefinition): Promise<string | null> {
  // Skip query generation if all operations are disabled
  const hasQueries = entity.operations.get || entity.operations.list || 
    (entity.operations.custom && Object.values(entity.operations.custom).some(op => op.type === 'query'));
  
  if (!hasQueries) {
    return null;
  }
  
  // For now, return the queries as-is since they need manual integration
  const queries = await generateQueries(entity);
  return queries;
}

/**
 * Update the mutations __init__.py file to include generated mutations
 */
async function updateMutationsInit(entities: EntityDefinition[]): Promise<void> {
  console.log('\n📝 Updating mutations __init__.py...');
  
  const initPath = path.join(OUTPUT_PATHS.serverMutations, '__init__.py');
  
  // Read existing content
  let content = '';
  try {
    content = await fs.readFile(initPath, 'utf-8');
  } catch (e) {
    console.warn('Could not read existing mutations __init__.py');
  }
  
  // Generate import statements for new mutations
  const newImports = entities.map(entity => 
    `from .${entity.name.toLowerCase()}_mutation import ${entity.name}Mutations`
  );
  
  // Check which imports are missing
  const missingImports = newImports.filter(imp => !content.includes(imp));
  
  if (missingImports.length === 0) {
    console.log('All entity mutations already imported');
    return;
  }
  
  console.log(`\n⚠️  Add these imports to ${initPath}:`);
  missingImports.forEach(imp => console.log(`   ${imp}`));
  
  console.log(`\n⚠️  And update the Mutation class to include:`);
  entities.forEach(entity => {
    console.log(`   ${entity.name}Mutations,`);
  });
}

/**
 * Generate type additions that need to be added to generated_types.py
 */
async function generateTypesAddendum(entities: EntityDefinition[]): Promise<void> {
  console.log('\n📝 Generating type additions...');
  
  const additions: string[] = [];
  
  for (const entity of entities) {
    const entityTypes = await generateTypeAdditions(entity);
    additions.push(`\n# Types for ${entity.name}\n${entityTypes}`);
  }
  
  const addendumPath = path.join(OUTPUT_PATHS.serverTypes, 'generated_types_additions.py');
  const content = `"""
Additional GraphQL types for generated entities.
Add these to the main generated_types.py file.
"""

from datetime import datetime
from typing import NewType
import strawberry

# Import existing types from generated_types
from .generated_types import (
    DiagramID,
    NodeID,
    HandleID,
    JSONScalar,
    MutationResult,
    PersonType,
    NodeType,
    DiagramType,
    ExecutionType,
    HandleType,
    ArrowType,
    ApiKeyType,
)

${additions.join('\n\n')}

# Add these to the __all__ export at the bottom of generated_types.py:
__all_additions__ = [
${entities.flatMap(entity => [
    `    "${entity.name}ID",`,
    `    "Create${entity.name}Input",`,
    `    "Update${entity.name}Input",`,
    `    "${entity.name}Result",`,
    `    "${entity.name}Type",`,
    entity.operations.list && typeof entity.operations.list === 'object' && entity.operations.list.filters && entity.operations.list.filters.length > 0 ? 
    `    "${entity.name}FilterInput",` : null
  ].filter(Boolean)).join('\n')}
]
`;
  
  await writeGeneratedFile(addendumPath, content);
  
  console.log(`\n⚠️  Review ${path.relative(process.cwd(), addendumPath)} and integrate the types into generated_types.py`);
}

/**
 * Generate instructions for manual integration
 */
async function generateIntegrationInstructions(entities: EntityDefinition[]): Promise<void> {
  const instructionsPath = path.join(OUTPUT_PATHS.serverQueries, 'INTEGRATION_INSTRUCTIONS.md');
  
  const queryMethods = entities.flatMap(entity => {
    const methods = [];
    if (entity.operations.get) {
      methods.push(`    - ${entity.name.toLowerCase()}(id) -> ${entity.name}Type`);
    }
    if (entity.operations.list) {
      methods.push(`    - ${entity.plural}(filter, limit, offset) -> list[${entity.name}Type]`);
    }
    return methods;
  });
  
  // Filter entities with queries
  const entitiesWithQueries = entities.filter(entity => 
    entity.operations.get || entity.operations.list || 
    (entity.operations.custom && Object.values(entity.operations.custom).some(op => op.type === 'query'))
  );

  const content = `# Entity Code Generation - Integration Instructions

## Generated Files

The following files have been generated:

### Mutations
${entities.map(e => `- mutations/${e.name.toLowerCase()}_mutation.py`).join('\n')}

### Query Methods  
${entitiesWithQueries.map(e => `- queries/${e.name.toLowerCase()}_queries.py`).join('\n')}

### Types
- generated_types_additions.py (merge into generated_types.py)

## Integration Steps

### 1. Update mutations/__init__.py

Add imports:
\`\`\`python
${entities.map(e => `from .${e.name.toLowerCase()}_mutation import ${e.name}Mutations`).join('\n')}
\`\`\`

Update the Mutation class inheritance:
\`\`\`python
@strawberry.type
class Mutation(
    ApiKeyMutations,
    DiagramMutations,
    ExecutionMutations,
    NodeMutations,
    PersonMutations,
    UploadMutations,
${entities.map(e => `    ${e.name}Mutations,`).join('\n')}
):
    """Combined GraphQL mutation type."""
    pass
\`\`\`

### 2. Update queries.py

Add the query methods from the generated query files to the main Query class:
${queryMethods.join('\n')}

### 3. Update generated_types.py

1. Add the types from generated_types_additions.py
2. Update the __all__ export to include the new types

### 4. Create Services

Ensure these services exist in the service registry:
${entities.map(e => `- ${e.service?.name || e.name.toLowerCase() + '_service'}`).join('\n')}

## Notes

- The generated code assumes services follow the pattern \`{entity}_service\`
- Custom logic in mutations may reference additional services (notification_service, email_service, etc.)
- Review and adjust the generated code as needed for your specific requirements
`;
  
  await writeGeneratedFile(instructionsPath, content);
  console.log(`\n📋 Integration instructions written to: ${path.relative(process.cwd(), instructionsPath)}`);
}

/**
 * Generate frontend exports for hooks
 */
async function generateFrontendExports(entities: EntityDefinition[]): Promise<void> {
  console.log('\n📦 Generating frontend exports...');
  
  const exports = entities.map(entity => 
    `export * from './use${entity.name}Operations';`
  ).join('\n');
  
  const indexContent = `// Auto-generated barrel exports for entity hooks
${exports}
`;
  
  const hooksIndexPath = path.join(OUTPUT_PATHS.hooks, 'hooks', 'index.ts');
  await writeGeneratedFile(hooksIndexPath, indexContent);
}

/**
 * Run the integration script to automatically integrate generated code
 */
async function runIntegrationScript(): Promise<boolean> {
  console.log('\n🔧 Running automatic integration...');
  
  try {
    const scriptPath = path.join(path.dirname(fileURLToPath(import.meta.url)), 'integrate-generated-entities.py');
    const serverPath = path.dirname(PATHS.serverGraphQLDir);
    
    // Check if script exists
    try {
      await fs.access(scriptPath);
    } catch {
      console.warn('⚠️  Integration script not found. Skipping automatic integration.');
      return false;
    }
    
    // Run the integration script
    const output = execSync(`python3 ${scriptPath} --server-path ${serverPath}`, {
      encoding: 'utf-8',
      stdio: 'pipe'
    });
    
    console.log(output);
    console.log('✅ Automatic integration completed!');
    return true;
  } catch (error: any) {
    console.error('❌ Automatic integration failed:', error.message);
    if (error.stdout) {
      console.log('Output:', error.stdout.toString());
    }
    if (error.stderr) {
      console.error('Error:', error.stderr.toString());
    }
    return false;
  }
}

/**
 * Main generation function
 */
async function main() {
  const quiet = process.env.QUIET === 'true';
  
  if (!quiet) {
    console.log('🚀 Starting entity code generation...\n');
  }
  
  try {
    // Load all entity definitions
    const entities = await loadEntityDefinitions();
    
    if (entities.length === 0) {
      console.warn('⚠️  No entity definitions found in src/entities/');
      return;
    }
    
    if (!quiet) {
      console.log(`Found ${entities.length} entity definition(s): ${entities.map(e => e.name).join(', ')}\n`);
    }
    
    // First, generate TypeScript interfaces for entities
    console.log('📝 Generating TypeScript interfaces for entities...');
    await generateEntityInterfaces(
      entities,
      path.join(PATHS.srcDir, 'generated-entities.ts')
    );
    console.log('✅ Entity interfaces generated. Run `make codegen` to generate Python models.');
    console.log('');
    
    // Generate code for each entity
    for (const entity of entities) {
      await generateEntityCode(entity);
    }
    
    // Update server-side integration files
    await updateMutationsInit(entities);
    await generateTypesAddendum(entities);
    await generateIntegrationInstructions(entities);
    
    // Generate frontend exports
    await generateFrontendExports(entities);
    
    // Try to run automatic integration
    const integrationSuccess = await runIntegrationScript();
    
    console.log('\n✅ Entity code generation completed!');
    
    if (!integrationSuccess) {
      console.log('\n⚠️  IMPORTANT: Manual integration required!');
      console.log('1. Review the INTEGRATION_INSTRUCTIONS.md file');
      console.log('2. Integrate the generated types into generated_types.py');
      console.log('3. Update mutations/__init__.py to include new mutation classes');
      console.log('4. Add query methods to the main Query class in queries.py');
      console.log('5. Ensure required services exist in the service registry');
    } else {
      console.log('\n✅ Code has been automatically integrated!');
      console.log('\n📋 Next steps:');
    }
    
    console.log('1. Run `make codegen` to generate Python models from TypeScript interfaces');
    console.log('2. Run GraphQL codegen to update frontend types');
    console.log('3. Review any service stubs that were created and implement the business logic');
    
  } catch (error) {
    console.error('\n❌ Entity code generation failed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

export { main as generateEntities, loadEntityDefinitions };