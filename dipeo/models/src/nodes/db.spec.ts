
import { NodeType } from '../core/enums/node-types.js';
import { DBBlockSubType, DBOperation, DataFormat } from '../core/enums/node-specific.js';
import { NodeSpecification } from '../node-specification.js';
import { textField, objectField, booleanField } from '../core/field-presets.js';
import { validatedEnumField } from '../core/validation-utils.js';

export const dbSpec: NodeSpecification = {
  nodeType: NodeType.DB,
  displayName: "Database",
  category: "integration",
  icon: "🗄️",
  color: "#795548",
  description: "Database operations",

  fields: [
    {
      name: "file",
      type: "any",
      required: false,
      description: "File path or array of file paths",
      uiConfig: {
        inputType: "text"
      }
    },
    textField({
      name: "collection",
      description: "Database collection name"
    }),
    validatedEnumField({
      name: "sub_type",
      description: "Database operation type",
      options: [
        { value: DBBlockSubType.FIXED_PROMPT, label: "Fixed Prompt" },
        { value: DBBlockSubType.FILE, label: "File" },
        { value: DBBlockSubType.CODE, label: "Code" },
        { value: DBBlockSubType.API_TOOL, label: "API Tool" }
      ],
      defaultValue: DBBlockSubType.FIXED_PROMPT,
      required: true
    }),
    validatedEnumField({
      name: "operation",
      description: "Operation configuration",
      options: [
        { value: DBOperation.PROMPT, label: "Prompt" },
        { value: DBOperation.READ, label: "Read" },
        { value: DBOperation.WRITE, label: "Write" },
        { value: DBOperation.APPEND, label: "Append" },
        { value: DBOperation.UPDATE, label: "Update" }
      ],
      defaultValue: DBOperation.READ,
      required: true
    }),
    textField({
      name: "query",
      description: "Query configuration"
    }),
    {
      name: "keys",
      type: "any",
      required: false,
      description: "Single key or list of dot-separated keys to target within the JSON payload",
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., user.profile.name or key1,key2"
      }
    },
    {
      name: "lines",
      type: "any",
      required: false,
      description: "Line selection or ranges to read (e.g., 1:120 or ['10:20'])",
      uiConfig: {
        inputType: "text",
        placeholder: "e.g., 1:120 or 5,10:20"
      }
    },
    objectField({
      name: "data",
      description: "Data configuration",
      required: false,
      collapsible: true
    }),
    booleanField({
      name: "serialize_json",
      description: "Serialize structured data to JSON string (for backward compatibility)",
      defaultValue: false
    }),
    validatedEnumField({
      name: "format",
      description: "Data format (json, yaml, csv, text, etc.)",
      options: [
        { value: DataFormat.JSON, label: "JSON" },
        { value: DataFormat.YAML, label: "YAML" },
        { value: DataFormat.CSV, label: "CSV" },
        { value: DataFormat.TEXT, label: "Text" },
        { value: DataFormat.XML, label: "XML" }
      ],
      defaultValue: DataFormat.JSON,
      required: false
    })
  ],

  handles: {
    inputs: ["default"],
    outputs: ["default"]
  },

  inputPorts: [
    {
      name: "default",
      contentType: "object",
      required: false,
      description: "Input data for database operations (query parameters, data to write/update)"
    }
  ],

  outputs: {
    result: {
      type: "any",
      description: "Node execution result"
    }
  },

  execution: {
    timeout: 300,
    retryable: true,
    maxRetries: 3
  },

  primaryDisplayField: "operation",

  handlerMetadata: {
    modulePath: "dipeo.application.execution.handlers.db",
    className: "DbHandler",
    mixins: ["LoggingMixin", "ValidationMixin", "ConfigurationMixin"],
    serviceKeys: ["DB_CLIENT", "FILE_SYSTEM", "STATE_STORE"]
  }
};
