// Auto-generated node registry
import { registerNodeConfig } from '@/features/diagram-editor/config/nodeRegistry';

import { startConfig } from '@/__generated__/nodes/startNodeConfig';
import { templateJobConfig } from '@/__generated__/nodes/template_jobNodeConfig';
import { hookConfig } from '@/__generated__/nodes/hookNodeConfig';
import { dbConfig } from '@/__generated__/nodes/dbNodeConfig';
import { apiJobConfig } from '@/__generated__/nodes/api_jobNodeConfig';
import { codeJobConfig } from '@/__generated__/nodes/code_jobNodeConfig';
import { typescriptAstConfig } from '@/__generated__/nodes/typescript_astNodeConfig';
import { userResponseConfig } from '@/__generated__/nodes/user_responseNodeConfig';
import { conditionConfig } from '@/__generated__/nodes/conditionNodeConfig';
import { subDiagramConfig } from '@/__generated__/nodes/sub_diagramNodeConfig';
import { shellJobConfig } from '@/__generated__/nodes/shell_jobNodeConfig';
import { jsonSchemaValidatorConfig } from '@/__generated__/nodes/json_schema_validatorNodeConfig';
import { personJobConfig } from '@/__generated__/nodes/person_jobNodeConfig';
import { endpointConfig } from '@/__generated__/nodes/endpointNodeConfig';

export function registerAllNodes() {
  registerNodeConfig(startConfig);
  registerNodeConfig(templateJobConfig);
  registerNodeConfig(hookConfig);
  registerNodeConfig(dbConfig);
  registerNodeConfig(apiJobConfig);
  registerNodeConfig(codeJobConfig);
  registerNodeConfig(typescriptAstConfig);
  registerNodeConfig(userResponseConfig);
  registerNodeConfig(conditionConfig);
  registerNodeConfig(subDiagramConfig);
  registerNodeConfig(shellJobConfig);
  registerNodeConfig(jsonSchemaValidatorConfig);
  registerNodeConfig(personJobConfig);
  registerNodeConfig(endpointConfig);
}

// Call this on app initialization
registerAllNodes();
