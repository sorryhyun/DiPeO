/**
 * TypeScript AST Parser node specification
 */

import { NodeType } from '../core/enums/node-types.js';
import { SupportedLanguage } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';

export const typescriptAstSpec: NodeSpecification = {
  nodeType: NodeType.TYPESCRIPT_AST,
  displayName: "TypeScript AST Parser",
  category: "codegen",
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
    },
    {
      name: "transformEnums",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Transform enum definitions to a simpler format",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "flattenOutput",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Flatten the output structure for easier consumption",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "outputFormat",
      type: "enum",
      required: false,
      defaultValue: "standard",
      description: "Output format for the parsed data",
      validation: {
        allowedValues: ["standard", "for_codegen", "for_analysis"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: "standard", label: "Standard" },
          { value: "for_codegen", label: "For Code Generation" },
          { value: "for_analysis", label: "For Analysis" }
        ]
      }
    },
    {
      name: "batch",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Enable batch processing mode",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "batchInputKey",
      type: "string",
      required: false,
      defaultValue: "sources",
      description: "Key to extract batch items from input",
      uiConfig: {
        inputType: "text"
      }
    }
  ],

  handles: {
    inputs: ["default"],
    outputs: ["results", "error"]
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
  ],

  primaryDisplayField: "parseMode"
};
