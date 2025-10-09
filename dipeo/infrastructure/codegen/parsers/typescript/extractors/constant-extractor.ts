/**
 * Constant extractor for TypeScript AST
 */

import { SourceFile, Node, SyntaxKind } from 'ts-morph'
import type { ConstantInfo, EnumInfo } from '@dipeo/models/src/codegen/ast-types'
import { getJSDoc, parseExpression, setConstValueMap, clearConstValueMap, setEnumValueMap, clearEnumValueMap } from './utils'

/**
 * Parse imported helper functions and add them to the const map
 * This allows imported functions like validatedEnumField, objectField, textField to be evaluated
 */
function parseImportedHelpers(sourceFile: SourceFile, constMap: Map<string, any>): void {
  // Get all import declarations
  const importDeclarations = sourceFile.getImportDeclarations()

  for (const importDecl of importDeclarations) {
    const moduleSpecifier = importDecl.getModuleSpecifierValue()

    // Only process our known helper modules
    if (!moduleSpecifier.includes('field-presets') && !moduleSpecifier.includes('validation-utils')) {
      continue
    }

    // Get all named imports
    const namedImports = importDecl.getNamedImports()

    for (const namedImport of namedImports) {
      const name = namedImport.getName()

      // Create a wrapper for known helper functions based on name
      // We don't need to resolve the actual TypeScript source
      const helperFunction = createHelperFunction(name, null)
      if (helperFunction) {
        constMap.set(name, helperFunction)
      }
    }
  }
}

/**
 * Create a JavaScript wrapper for known helper functions
 * This allows them to be called during expression parsing
 */
function createHelperFunction(name: string, declaration: Node | null): Function | null {
  // For known helper functions, create a function that returns the expected field spec structure
  // We don't use the declaration parameter - we just implement based on the function name

  if (name === 'validatedEnumField') {
    return (options: any) => ({
      name: options.name,
      type: 'enum',
      required: options.required !== undefined ? options.required : true,
      ...(options.defaultValue !== undefined && { defaultValue: options.defaultValue }),
      description: options.description,
      validation: {
        allowedValues: options.options ? options.options.map((opt: any) => opt.value) : []
      },
      uiConfig: {
        inputType: 'select',
        options: options.options || [],
        ...(options.column && { column: options.column })
      },
      ...(options.conditional && { conditional: options.conditional })
    })
  }

  if (name === 'objectField') {
    return (options: any) => ({
      name: options.name,
      type: 'object',
      required: options.required !== undefined ? options.required : false,
      description: options.description,
      uiConfig: {
        inputType: options.language ? 'code' : 'code',
        ...(options.language && { language: options.language }),
        collapsible: options.collapsible !== undefined ? options.collapsible : true
      }
    })
  }

  if (name === 'textField') {
    return (options: any) => ({
      name: options.name,
      type: 'string',
      required: options.required !== undefined ? options.required : false,
      ...(options.defaultValue !== undefined && { defaultValue: options.defaultValue }),
      description: options.description,
      uiConfig: {
        inputType: 'text',
        ...(options.placeholder && { placeholder: options.placeholder }),
        ...(options.column && { column: options.column })
      }
    })
  }

  if (name === 'validatedNumberField' || name === 'numberField') {
    return (options: any) => ({
      name: options.name,
      type: 'number',
      required: options.required !== undefined ? options.required : false,
      ...(options.defaultValue !== undefined && { defaultValue: options.defaultValue }),
      description: options.description,
      ...(options.min !== undefined || options.max !== undefined ? {
        validation: {
          ...(options.min !== undefined && { min: options.min }),
          ...(options.max !== undefined && { max: options.max })
        }
      } : {}),
      uiConfig: {
        inputType: 'number',
        ...(options.min !== undefined && { min: options.min }),
        ...(options.max !== undefined && { max: options.max }),
        ...(options.placeholder && { placeholder: options.placeholder }),
        ...(options.column && { column: options.column })
      }
    })
  }

  if (name === 'personField') {
    return (options: any = {}) => ({
      name: 'person',
      type: 'PersonID',
      required: false,
      description: 'AI person to use for this task',
      uiConfig: {
        inputType: 'personSelect'
      },
      ...options
    })
  }

  if (name === 'contentField') {
    return (options: any) => ({
      name: options.name || 'content',
      type: 'string',
      required: options.required !== undefined ? options.required : false,
      description: options.description || 'Inline content',
      uiConfig: {
        inputType: options.inputType || 'textarea',
        ...(options.placeholder && { placeholder: options.placeholder }),
        ...(options.rows && { rows: options.rows }),
        adjustable: true,
        ...(options.language && { language: options.language })
      }
    })
  }

  if (name === 'promptWithFileField') {
    return (options: any = {}) => {
      const name = options.name || 'default_prompt'
      const fileFieldName = options.fileFieldName || 'prompt_file'
      const description = options.description || 'Prompt template'
      const placeholder = options.placeholder || 'Enter prompt template...'
      const rows = options.rows || 10
      const column = options.column || 2
      const required = options.required || false

      return [
        {
          name,
          type: 'string',
          required,
          description,
          uiConfig: {
            inputType: 'textarea',
            placeholder,
            column,
            rows,
            adjustable: true,
            showPromptFileButton: true
          }
        },
        {
          name: fileFieldName,
          type: 'string',
          required: false,
          description: `Path to prompt file in /files/prompts/`,
          uiConfig: {
            inputType: 'text',
            placeholder: 'example.txt',
            column,
            hidden: true
          }
        }
      ]
    }
  }

  if (name === 'memoryControlFields') {
    return (options: any = {}) => {
      const fields: any[] = [
        {
          name: 'memorize_to',
          type: 'string',
          required: false,
          ...(options.defaultMemorizeTo && { defaultValue: options.defaultMemorizeTo }),
          description: 'Criteria used to select helpful messages for this task. Empty = memorize all. Special: \'GOLDFISH\' for goldfish mode. Comma-separated for multiple criteria.',
          uiConfig: {
            inputType: 'text',
            placeholder: 'e.g., requirements, acceptance criteria, API keys',
            column: 2
          }
        },
        {
          name: 'at_most',
          type: 'number',
          required: false,
          description: 'Select at most N messages to keep (system messages may be preserved in addition).',
          validation: {
            min: 1,
            max: options.maxAtMost || 500
          },
          uiConfig: {
            inputType: 'number',
            min: 1,
            max: options.maxAtMost || 500,
            column: 1
          }
        }
      ]

      if (options.includeIgnorePerson) {
        fields.push({
          name: 'ignore_person',
          type: 'string',
          required: false,
          description: 'Comma-separated list of person IDs whose messages should be excluded from memory selection.',
          uiConfig: {
            inputType: 'text',
            placeholder: 'e.g., assistant, user2',
            column: 2
          }
        })
      }

      return fields
    }
  }

  if (name === 'batchExecutionFields') {
    return (options: any = {}) => {
      return [
        {
          name: 'batch',
          type: 'boolean',
          required: false,
          defaultValue: false,
          description: 'Enable batch mode for processing multiple items',
          uiConfig: {
            inputType: 'checkbox'
          }
        },
        {
          name: 'batch_input_key',
          type: 'string',
          required: false,
          defaultValue: options.defaultBatchInputKey || 'items',
          description: 'Key containing the array to iterate over in batch mode',
          uiConfig: {
            inputType: 'text',
            placeholder: options.defaultBatchInputKey || 'items'
          }
        },
        {
          name: 'batch_parallel',
          type: 'boolean',
          required: false,
          defaultValue: true,
          description: 'Execute batch items in parallel',
          uiConfig: {
            inputType: 'checkbox'
          }
        },
        {
          name: 'max_concurrent',
          type: 'number',
          required: false,
          defaultValue: options.defaultMaxConcurrent || 10,
          description: 'Maximum concurrent executions in batch mode',
          validation: {
            min: 1,
            max: options.maxConcurrentLimit || 100
          },
          uiConfig: {
            inputType: 'number',
            min: 1,
            max: options.maxConcurrentLimit || 100
          }
        }
      ]
    }
  }

  if (name === 'timeoutField') {
    return (options: any = {}) => {
      const {
        name = 'timeout',
        description = 'Operation timeout in seconds',
        defaultValue,
        min = 0,
        max = 3600,
        required = false
      } = options

      return {
        name,
        type: 'number',
        required,
        ...(defaultValue !== undefined && { defaultValue }),
        description,
        ...(min !== undefined || max !== undefined ? {
          validation: {
            ...(min !== undefined && { min }),
            ...(max !== undefined && { max })
          }
        } : {}),
        uiConfig: {
          inputType: 'number',
          ...(min !== undefined && { min }),
          ...(max !== undefined && { max })
        }
      }
    }
  }

  if (name === 'filePathField') {
    return (options: any = {}) => {
      const {
        name = 'file_path',
        description = 'Path to file',
        placeholder = '/path/to/file',
        required = false
      } = options

      return {
        name,
        type: 'string',
        required,
        description,
        uiConfig: {
          inputType: 'text',
          placeholder
        }
      }
    }
  }

  if (name === 'booleanField') {
    return (options: any) => {
      const {
        name,
        description,
        defaultValue = false,
        required = false
      } = options

      return {
        name,
        type: 'boolean',
        required,
        defaultValue,
        description,
        uiConfig: {
          inputType: 'checkbox'
        }
      }
    }
  }

  if (name === 'fileOrContentFields') {
    return (options: any = {}) => {
      const {
        fileFieldName = 'file_path',
        contentFieldName = 'content',
        fileDescription = 'Path to file',
        contentDescription = 'Inline content (alternative to file_path)',
        contentPlaceholder = 'Enter content...',
        contentInputType = 'textarea',
        language,
        rows = 10
      } = options

      return [
        {
          name: fileFieldName,
          type: 'string',
          required: false,
          description: fileDescription,
          uiConfig: {
            inputType: 'text',
            placeholder: '/path/to/file'
          }
        },
        {
          name: contentFieldName,
          type: 'string',
          required: false,
          description: contentDescription,
          uiConfig: {
            inputType: contentInputType,
            placeholder: contentPlaceholder,
            rows,
            adjustable: true,
            ...(language && { language })
          }
        }
      ]
    }
  }

  if (name === 'enumSelectField') {
    return (options: any) => {
      const {
        name,
        description,
        options: selectOptions,
        defaultValue,
        required = true,
        column
      } = options

      const allowedValues = selectOptions ? selectOptions.map((opt: any) => opt.value) : []

      return {
        name,
        type: 'enum',
        required,
        ...(defaultValue !== undefined && { defaultValue }),
        description,
        validation: {
          allowedValues
        },
        uiConfig: {
          inputType: 'select',
          options: selectOptions || [],
          ...(column && { column })
        }
      }
    }
  }

  if (name === 'validatedTextField') {
    return (options: any) => {
      const {
        name,
        description,
        pattern,
        minLength,
        maxLength,
        placeholder,
        required = false,
        defaultValue,
        column
      } = options

      const hasValidation = pattern || minLength !== undefined || maxLength !== undefined

      return {
        name,
        type: 'string',
        required,
        ...(defaultValue !== undefined && { defaultValue }),
        description,
        ...(hasValidation ? {
          validation: {
            ...(pattern && { pattern }),
            ...(minLength !== undefined && { minLength }),
            ...(maxLength !== undefined && { maxLength })
          }
        } : {}),
        uiConfig: {
          inputType: 'text',
          ...(placeholder && { placeholder }),
          ...(column && { column })
        }
      }
    }
  }

  if (name === 'validatedArrayField') {
    return (options: any) => {
      const {
        name,
        description,
        itemType,
        inputType = 'text',
        placeholder,
        required = false,
        conditional
      } = options

      return {
        name,
        type: 'array',
        required,
        description,
        validation: {
          itemType
        },
        uiConfig: {
          inputType,
          ...(placeholder && { placeholder })
        },
        ...(conditional && { conditional })
      }
    }
  }

  return null
}

export function parseConstants(sourceFile: SourceFile, includeJSDoc: boolean, enums?: EnumInfo[]): ConstantInfo[] {
  const constants: ConstantInfo[] = []
  const constMap = new Map<string, any>()

  // Build enum value map if enums are provided
  const enumMap = new Map<string, any>()
  if (enums) {
    for (const enumDef of enums) {
      for (const member of enumDef.members) {
        const key = `${enumDef.name}.${member.name}`
        enumMap.set(key, member.value)
      }
    }
  }

  // Set the enum map for resolution during expression parsing
  setEnumValueMap(enumMap)

  // Parse imported helper functions and add them to the const map FIRST
  // This must happen before parsing any declarations
  parseImportedHelpers(sourceFile, constMap)

  // Set the const map so helper functions are available during expression parsing
  setConstValueMap(constMap)

  // First pass: collect all const declarations without resolving references
  const constDeclarations: Array<{
    name: string
    type: string
    initializer: Node | undefined
    varDecl: any
    isExported?: boolean
  }> = []

  sourceFile.getVariableDeclarations().forEach(varDecl => {
    // Only process const declarations
    const statement = varDecl.getVariableStatement()
    if (!statement || statement.getDeclarationKind() !== 'const') {
      return
    }

    // Check if it's exported (we'll track this but parse all consts)
    const isExported = statement.isExported()

    const name = varDecl.getName()
    const type = varDecl.getType().getText(varDecl)
    const initializer = varDecl.getInitializer()

    constDeclarations.push({
      name,
      type,
      initializer,
      varDecl,
      isExported
    })
  })

  // Process declarations in order, building up the const map
  // This allows later consts to reference earlier ones
  constDeclarations.forEach(({ name, type, initializer, varDecl, isExported }) => {
    let value: any = undefined

    // Set the current const map for resolution
    setConstValueMap(constMap)

    if (initializer) {
      try {
        // Parse the expression with const resolution enabled
        value = parseExpression(initializer)
      } catch (e) {
        // If parsing fails, store the text representation
        value = initializer.getText()
      }
    }

    // Add this const's value to the map for future references
    constMap.set(name, value)

    constants.push({
      name,
      type,
      value,
      isExported: isExported || false,
      jsDoc: includeJSDoc ? getJSDoc(varDecl) : undefined
    })
  })

  // Clear the maps after parsing
  clearConstValueMap()
  clearEnumValueMap()

  return constants
}
