/**
 * TypeScript AST Parser node specification
 */

import { NodeType } from '../core/enums/node-types.js';
import { SupportedLanguage, TypeScriptExtractPattern, TypeScriptParseMode, TypeScriptOutputFormat } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import { contentField, booleanField, textField } from '../core/field-presets.js';
import { validatedEnumField } from '../core/validation-utils.js';

export const typescriptAstSpec: NodeSpecification = {
  nodeType: NodeType.TYPESCRIPT_AST,
  displayName: "TypeScript AST Parser",
  category: "codegen",
  icon: "🔍",
  color: "#3178c6",
  description: "Parses TypeScript source code and extracts AST, interfaces, types, and enums",

  fields: [
    contentField({
      name: "source",
      description: "TypeScript source code to parse",
      inputType: "code",
      language: SupportedLanguage.TYPESCRIPT
    }),
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
        inputType: "code"
      }
    },
    booleanField({
      name: "include_jsdoc",
      description: "Include JSDoc comments in the extracted data",
      defaultValue: false
    }),
    validatedEnumField({
      name: "parse_mode",
      description: "TypeScript parsing mode",
      options: [
        { value: TypeScriptParseMode.MODULE, label: "Module" },
        { value: TypeScriptParseMode.SCRIPT, label: "Script" }
      ],
      defaultValue: TypeScriptParseMode.MODULE,
      required: false
    }),
    booleanField({
      name: "transform_enums",
      description: "Transform enum definitions to a simpler format",
      defaultValue: false
    }),
    booleanField({
      name: "flatten_output",
      description: "Flatten the output structure for easier consumption",
      defaultValue: false
    }),
    validatedEnumField({
      name: "output_format",
      description: "Output format for the parsed data",
      options: [
        { value: TypeScriptOutputFormat.STANDARD, label: "Standard" },
        { value: TypeScriptOutputFormat.FOR_CODEGEN, label: "For Code Generation" },
        { value: TypeScriptOutputFormat.FOR_ANALYSIS, label: "For Analysis" }
      ],
      defaultValue: TypeScriptOutputFormat.STANDARD,
      required: false
    }),
    booleanField({
      name: "batch",
      description: "Enable batch processing mode",
      defaultValue: false
    }),
    textField({
      name: "batch_input_key",
      description: "Key to extract batch items from input",
      defaultValue: "sources"
    })
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
