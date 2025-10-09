/**
 * TypeScript AST Parser node specification
 */

import { NodeType } from '../core/enums/node-types.js';
import { SupportedLanguage, TypeScriptExtractPattern, TypeScriptParseMode, TypeScriptOutputFormat } from '../core/enums/node-specific.js';
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
      required: false,
      description: "TypeScript source code to parse",
      uiConfig: {
        inputType: "code",
        language: SupportedLanguage.TYPESCRIPT
      }
    },
    {
      name: "extract_patterns",
      type: "array",
      required: false,
      defaultValue: [TypeScriptExtractPattern.INTERFACE, TypeScriptExtractPattern.TYPE, TypeScriptExtractPattern.ENUM],
      description: "Patterns to extract from the AST",
      validation: {
        itemType: "enum",
        allowedValues: ["interface", "type", "enum", "class", "function", "const", "export"]
      },
      uiConfig: {
        inputType: "code",
      }
    },
    {
      name: "include_jsdoc",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Include JSDoc comments in the extracted data",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "parse_mode",
      type: "enum",
      required: false,
      defaultValue: TypeScriptParseMode.MODULE,
      description: "TypeScript parsing mode",
      validation: {
        allowedValues: ["module", "script"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: TypeScriptParseMode.MODULE, label: "Module" },
          { value: TypeScriptParseMode.SCRIPT, label: "Script" }
        ]
      }
    },
    {
      name: "transform_enums",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Transform enum definitions to a simpler format",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "flatten_output",
      type: "boolean",
      required: false,
      defaultValue: false,
      description: "Flatten the output structure for easier consumption",
      uiConfig: {
        inputType: "checkbox"
      }
    },
    {
      name: "output_format",
      type: "enum",
      required: false,
      defaultValue: TypeScriptOutputFormat.STANDARD,
      description: "Output format for the parsed data",
      validation: {
        allowedValues: ["standard", "for_codegen", "for_analysis"]
      },
      uiConfig: {
        inputType: "select",
        options: [
          { value: TypeScriptOutputFormat.STANDARD, label: "Standard" },
          { value: TypeScriptOutputFormat.FOR_CODEGEN, label: "For Code Generation" },
          { value: TypeScriptOutputFormat.FOR_ANALYSIS, label: "For Analysis" }
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
      name: "batch_input_key",
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

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "TypeScript source code or configuration (source code as string, or object with source and options)"
    }
  ],

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
        extract_patterns: [TypeScriptExtractPattern.INTERFACE]
      }
    },
    {
      name: "Parse Multiple Types",
      description: "Extract interfaces, types, and enums",
      configuration: {
        source: "interface User { id: string; }\ntype Status = 'active' | 'inactive';\nenum Role { Admin, User }",
        extract_patterns: [TypeScriptExtractPattern.INTERFACE, TypeScriptExtractPattern.TYPE, TypeScriptExtractPattern.ENUM],
        include_jsdoc: true
      }
    }
  ],

  primaryDisplayField: "parse_mode",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.typescript_ast",
    className: "TypescriptAstHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["FILE_SYSTEM", "STATE_STORE"]
  }
};
