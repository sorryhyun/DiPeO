/**
 * TypeScript AST Parser node specification
 */

import { NodeType, SupportedLanguage } from '../diagram.js';
import { NodeSpecification } from '../node-specifications.js';

export const typescriptAstSpec: NodeSpecification = {
  nodeType: NodeType.TYPESCRIPT_AST,
  displayName: "TypeScript AST Parser",
  category: "utility",
  icon: "🔍",
  color: "#3178c6",
  description: "Parses TypeScript source code and extracts AST, interfaces, types, and enums",
  
  fields: [
    {
      name: "source",
      type: "string",
      required: true,
      description: "TypeScript source code to parse",
      uiConfig: {
        inputType: "code",
        language: SupportedLanguage.TYPESCRIPT
      }
    },
    {
      name: "extractPatterns",
      type: "array",
      required: false,
      defaultValue: ["interface", "type", "enum"],
      description: "Patterns to extract from the AST",
      validation: {
        itemType: "string",
        allowedValues: ["interface", "type", "enum", "class", "function", "const", "export"]
      },
      uiConfig: {
        inputType: "code",
      }
    },
    {
      name: "includeJSDoc",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Include JSDoc comments in the extracted data",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "parseMode",
      type: "enum",
      required: false,
      defaultValue: "module",
      description: "TypeScript parsing mode",
      validation: {
        allowedValues: ["module", "script"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "module", label: "Module" },
          { value: "script", label: "Script" }
        ]
      }
    }
  ],
  
  handles: {
    inputs: ["source"],
    outputs: ["ast", "interfaces", "types", "enums", "error"]
  },
  
  outputs: {
    ast: {
      type: "any",
      description: "Parsed AST structure"
    },
    interfaces: {
      type: "any",
      description: "Extracted interface definitions"
    },
    types: {
      type: "any",
      description: "Extracted type aliases"
    },
    enums: {
      type: "any",
      description: "Extracted enum definitions"
    },
    error: {
      type: "any",
      description: "Error message if parsing fails"
    }
  },
  
  execution: {
    timeout: 30,
    retryable: false,
    maxRetries: 0
  },
  
  examples: [
    {
      name: "Parse Interface",
      description: "Extract interface from TypeScript code",
      configuration: {
        source: "interface User {\n  id: string;\n  name: string;\n  age?: number;\n}",
        extractPatterns: ["interface"]
      }
    },
    {
      name: "Parse Multiple Types",
      description: "Extract interfaces, types, and enums",
      configuration: {
        source: "interface User { id: string; }\ntype Status = 'active' | 'inactive';\nenum Role { Admin, User }",
        extractPatterns: ["interface", "type", "enum"],
        includeJSDoc: true
      }
    }
  ]
};