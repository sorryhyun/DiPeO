#!/usr/bin/env tsx
/**
 * TypeScript AST parser using ts-morph
 * Parses TypeScript source code and extracts interfaces, types, enums, etc.
 */

import { Project, SourceFile, Node } from 'ts-morph'
import * as fs from 'fs'

interface ParseResult {
  ast: any
  interfaces: InterfaceInfo[]
  types: TypeAliasInfo[]
  enums: EnumInfo[]
  classes?: ClassInfo[]
  functions?: FunctionInfo[]
  constants?: ConstantInfo[]
  error?: string
}

interface InterfaceInfo {
  name: string
  properties: PropertyInfo[]
  extends?: string[]
  isExported: boolean
  jsDoc?: string
}

interface PropertyInfo {
  name: string
  type: string
  optional: boolean
  readonly: boolean
  jsDoc?: string
}

interface TypeAliasInfo {
  name: string
  type: string
  isExported: boolean
  jsDoc?: string
}

interface EnumInfo {
  name: string
  members: { name: string; value?: string | number }[]
  isExported: boolean
  jsDoc?: string
}

interface ClassInfo {
  name: string
  properties: PropertyInfo[]
  methods: MethodInfo[]
  extends?: string
  implements?: string[]
  isExported: boolean
  jsDoc?: string
}

interface MethodInfo {
  name: string
  parameters: ParameterInfo[]
  returnType: string
  isAsync: boolean
  jsDoc?: string
}

interface ParameterInfo {
  name: string
  type: string
  optional: boolean
  defaultValue?: string
}

interface FunctionInfo {
  name: string
  parameters: ParameterInfo[]
  returnType: string
  isAsync: boolean
  isExported: boolean
  jsDoc?: string
}

interface ConstantInfo {
  name: string
  type: string
  value: any
  isExported: boolean
  jsDoc?: string
}

function getJSDoc(node: Node): string | undefined {
  // Check if the node has JSDoc support
  if ('getJsDocs' in node && typeof node.getJsDocs === 'function') {
    const jsDocs = (node as any).getJsDocs()
    if (jsDocs.length > 0) {
      return jsDocs[0].getDescription().trim()
    }
  }
  return undefined
}

function parseInterfaces(sourceFile: SourceFile, includeJSDoc: boolean): InterfaceInfo[] {
  const interfaces: InterfaceInfo[] = []
  
  sourceFile.getInterfaces().forEach(interfaceDecl => {
    const properties: PropertyInfo[] = []
    
    interfaceDecl.getProperties().forEach(prop => {
      // Get the type node to preserve original syntax (e.g., DomainNode[] instead of resolved type)
      const typeNode = prop.getTypeNode()
      const typeText = typeNode ? typeNode.getText() : prop.getType().getText(prop)
      
      properties.push({
        name: prop.getName(),
        type: typeText,
        optional: prop.hasQuestionToken(),
        readonly: prop.isReadonly(),
        jsDoc: includeJSDoc ? getJSDoc(prop) : undefined
      })
    })
    
    interfaces.push({
      name: interfaceDecl.getName(),
      properties,
      extends: interfaceDecl.getExtends().map(e => e.getText()),
      isExported: interfaceDecl.isExported(),
      jsDoc: includeJSDoc ? getJSDoc(interfaceDecl) : undefined
    })
  })
  
  return interfaces
}

function parseTypeAliases(sourceFile: SourceFile, includeJSDoc: boolean): TypeAliasInfo[] {
  const types: TypeAliasInfo[] = []
  
  sourceFile.getTypeAliases().forEach(typeAlias => {
    // Get the type node to preserve original syntax
    const typeNode = typeAlias.getTypeNode()
    const typeText = typeNode ? typeNode.getText() : typeAlias.getType().getText(typeAlias)
    
    types.push({
      name: typeAlias.getName(),
      type: typeText,
      isExported: typeAlias.isExported(),
      jsDoc: includeJSDoc ? getJSDoc(typeAlias) : undefined
    })
  })
  
  return types
}

function parseEnums(sourceFile: SourceFile, includeJSDoc: boolean): EnumInfo[] {
  const enums: EnumInfo[] = []
  
  sourceFile.getEnums().forEach(enumDecl => {
    const members = enumDecl.getMembers().map(member => ({
      name: member.getName(),
      value: member.getValue()
    }))
    
    enums.push({
      name: enumDecl.getName(),
      members,
      isExported: enumDecl.isExported(),
      jsDoc: includeJSDoc ? getJSDoc(enumDecl) : undefined
    })
  })
  
  return enums
}

function parseClasses(sourceFile: SourceFile, includeJSDoc: boolean): ClassInfo[] {
  const classes: ClassInfo[] = []
  
  sourceFile.getClasses().forEach(classDecl => {
    const properties: PropertyInfo[] = []
    const methods: MethodInfo[] = []
    
    classDecl.getProperties().forEach(prop => {
      // Get the type node to preserve original syntax
      const typeNode = prop.getTypeNode()
      const typeText = typeNode ? typeNode.getText() : prop.getType().getText(prop)
      
      properties.push({
        name: prop.getName(),
        type: typeText,
        optional: prop.hasQuestionToken(),
        readonly: prop.isReadonly(),
        jsDoc: includeJSDoc ? getJSDoc(prop) : undefined
      })
    })
    
    classDecl.getMethods().forEach(method => {
      const parameters: ParameterInfo[] = method.getParameters().map(param => ({
        name: param.getName(),
        type: param.getType().getText(param),
        optional: param.isOptional(),
        defaultValue: param.getInitializer()?.getText()
      }))
      
      methods.push({
        name: method.getName(),
        parameters,
        returnType: method.getReturnType().getText(method),
        isAsync: method.isAsync(),
        jsDoc: includeJSDoc ? getJSDoc(method) : undefined
      })
    })
    
    classes.push({
      name: classDecl.getName() || 'Anonymous',
      properties,
      methods,
      extends: classDecl.getExtends()?.getText(),
      implements: classDecl.getImplements().map(i => i.getText()),
      isExported: classDecl.isExported(),
      jsDoc: includeJSDoc ? getJSDoc(classDecl) : undefined
    })
  })
  
  return classes
}

function parseFunctions(sourceFile: SourceFile, includeJSDoc: boolean): FunctionInfo[] {
  const functions: FunctionInfo[] = []
  
  sourceFile.getFunctions().forEach(func => {
    const parameters: ParameterInfo[] = func.getParameters().map(param => ({
      name: param.getName(),
      type: param.getType().getText(param),
      optional: param.isOptional(),
      defaultValue: param.getInitializer()?.getText()
    }))
    
    functions.push({
      name: func.getName() || 'Anonymous',
      parameters,
      returnType: func.getReturnType().getText(func),
      isAsync: func.isAsync(),
      isExported: func.isExported(),
      jsDoc: includeJSDoc ? getJSDoc(func) : undefined
    })
  })
  
  return functions
}

function parseConstants(sourceFile: SourceFile, includeJSDoc: boolean): ConstantInfo[] {
  const constants: ConstantInfo[] = []
  
  sourceFile.getVariableDeclarations().forEach(varDecl => {
    // Only process const declarations
    const statement = varDecl.getVariableStatement()
    if (!statement || !statement.isExported() || statement.getDeclarationKind() !== 'const') {
      return
    }
    
    const name = varDecl.getName()
    const type = varDecl.getType().getText(varDecl)
    const initializer = varDecl.getInitializer()
    
    let value: any = undefined
    
    if (initializer) {
      try {
        // Attempt to evaluate the initializer to get the actual value
        // For object literals, we'll parse them into a JavaScript object
        const initText = initializer.getText()
        
        // Use the proper expression parser
        value = parseExpression(initializer)
      } catch (e) {
        // If parsing fails, store the text representation
        value = initializer.getText()
      }
    }
    
    constants.push({
      name,
      type,
      value,
      isExported: true,
      jsDoc: includeJSDoc ? getJSDoc(varDecl) : undefined
    })
  })
  
  return constants
}

function parseObjectLiteral(node: Node): any {
  const result: any = {}
  
  // Use ts-morph's proper API to get object literal properties
  if (Node.isObjectLiteralExpression(node)) {
    const objLiteral = node
    
    objLiteral.getProperties().forEach(prop => {
      if (Node.isPropertyAssignment(prop)) {
        const propName = prop.getName()
        const propInit = prop.getInitializer()
        
        if (propInit) {
          result[propName] = parseExpression(propInit)
        }
      } else if (Node.isShorthandPropertyAssignment(prop)) {
        // Handle shorthand properties like { foo } where foo is a variable
        const propName = prop.getName()
        result[propName] = propName // Just use the name as value for now
      }
    })
  }
  
  return result
}

function parseExpression(node: Node): any {
  // Handle different expression types
  if (Node.isStringLiteral(node)) {
    return node.getLiteralValue()
  } else if (Node.isNumericLiteral(node)) {
    return node.getLiteralValue()
  } else if (node.getText() === 'true' || node.getText() === 'false') {
    return node.getText() === 'true'
  } else if (Node.isNullLiteral(node)) {
    return null
  } else if (Node.isObjectLiteralExpression(node)) {
    return parseObjectLiteral(node)
  } else if (Node.isArrayLiteralExpression(node)) {
    return parseArrayLiteral(node)
  } else if (Node.isPropertyAccessExpression(node)) {
    // Handle enum references like NodeType.PERSON_JOB
    return node.getText() // Keep as string representation
  } else if (Node.isIdentifier(node)) {
    // Handle simple identifiers
    return node.getText()
  } else {
    // For any other expression, return the text representation
    return node.getText()
  }
}

function parseArrayLiteral(node: Node): any[] {
  const result: any[] = []
  
  if (Node.isArrayLiteralExpression(node)) {
    node.getElements().forEach(element => {
      result.push(parseExpression(element))
    })
  }
  
  return result
}

function parsePrimitiveValue(text: string): any {
  // Remove quotes if present
  if ((text.startsWith('"') && text.endsWith('"')) || 
      (text.startsWith("'") && text.endsWith("'"))) {
    return text.slice(1, -1)
  }
  
  // Boolean
  if (text === 'true' || text === 'false') {
    return text === 'true'
  }
  
  // Number
  if (text.match(/^-?\d+(\.\d+)?$/)) {
    return parseFloat(text)
  }
  
  // Return as string for other cases
  return text
}

function parseTypeScript(
  source: string,
  extractPatterns: string[] = ['interface', 'type', 'enum'],
  includeJSDoc: boolean = false,
  parseMode: 'module' | 'script' = 'module'
): ParseResult {
  try {
    const project = new Project({
      useInMemoryFileSystem: true,
      compilerOptions: {
        target: 99, // ESNext
        module: parseMode === 'module' ? 99 : undefined,
        lib: ['esnext'],
        strict: true
      }
    })
    
    const sourceFile = project.createSourceFile('temp.ts', source)
    
    const result: ParseResult = {
      ast: {},
      interfaces: [],
      types: [],
      enums: []
    }
    
    // Extract based on requested patterns
    if (extractPatterns.includes('interface')) {
      result.interfaces = parseInterfaces(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('type')) {
      result.types = parseTypeAliases(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('enum')) {
      result.enums = parseEnums(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('class')) {
      result.classes = parseClasses(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('function')) {
      result.functions = parseFunctions(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('const') || extractPatterns.includes('constants')) {
      result.constants = parseConstants(sourceFile, includeJSDoc)
    }
    
    // Simple AST representation (for debugging/visualization)
    result.ast = {
      kind: sourceFile.getKindName(),
      childCount: sourceFile.getChildren().length,
      hasInterfaces: result.interfaces.length > 0,
      hasTypes: result.types.length > 0,
      hasEnums: result.enums.length > 0,
      hasClasses: (result.classes?.length || 0) > 0,
      hasFunctions: (result.functions?.length || 0) > 0,
      hasConstants: (result.constants?.length || 0) > 0
    }
    
    return result
  } catch (error) {
    return {
      ast: {},
      interfaces: [],
      types: [],
      enums: [],
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

// Batch parsing interfaces
interface BatchInput {
  sources: {
    [key: string]: string
  }
}

interface BatchResult {
  results: {
    [key: string]: ParseResult
  }
  metadata?: {
    totalFiles: number
    successCount: number
    failureCount: number
    processingTimeMs: number
  }
}

// Command line interface
const args = process.argv.slice(2)

// Extract file paths and options
const filePaths: string[] = []
const options = args.reduce((acc, arg) => {
  if (!arg.startsWith('--')) {
    filePaths.push(arg)
    return acc
  }
  if (arg.startsWith('--patterns=')) {
    acc.patterns = arg.substring(11).split(',')
  } else if (arg === '--include-jsdoc') {
    acc.includeJSDoc = true
  } else if (arg.startsWith('--mode=')) {
    acc.mode = arg.substring(7) as 'module' | 'script'
  } else if (arg === '--batch' || arg === '--batch-mode') {
    acc.batchMode = true
  } else if (arg.startsWith('--batch-input=')) {
    acc.batchInputFile = arg.substring(14)
  }
  return acc
}, {
  patterns: ['interface', 'type', 'enum'],
  includeJSDoc: false,
  mode: 'module' as 'module' | 'script',
  batchMode: false,
  batchInputFile: undefined as string | undefined
})

// Process batch input if provided
if (options.batchMode || options.batchInputFile) {
  const startTime = Date.now()
  
  try {
    let batchInput: BatchInput
    
    if (options.batchInputFile) {
      // Read batch input from JSON file
      const inputData = fs.readFileSync(options.batchInputFile, 'utf8')
      batchInput = JSON.parse(inputData)
    } else if (process.stdin.isTTY === false) {
      // Read from stdin if not a TTY
      const chunks: Buffer[] = []
      process.stdin.on('data', (chunk) => chunks.push(chunk))
      process.stdin.on('end', () => {
        try {
          const inputData = Buffer.concat(chunks).toString()
          batchInput = JSON.parse(inputData)
          processBatchInput(batchInput)
        } catch (error) {
          console.error(`Error parsing batch input: ${error}`)
          process.exit(1)
        }
      })
      // Exit here to wait for stdin
      process.stdin.resume()
    } else {
      console.error('Batch mode requires either --batch-input=<file> or input via stdin')
      process.exit(1)
    }
    
    if (options.batchInputFile) {
      processBatchInput(batchInput!)
    }
    
    function processBatchInput(input: BatchInput) {
      const results: BatchResult = {
        results: {},
        metadata: {
          totalFiles: 0,
          successCount: 0,
          failureCount: 0,
          processingTimeMs: 0
        }
      }
      
      // Process each source
      for (const [key, source] of Object.entries(input.sources)) {
        results.metadata!.totalFiles++
        
        try {
          // Check if source is a file path or TypeScript content
          let sourceContent: string
          if (source.includes('\n') || source.includes('import') || source.includes('export')) {
            // Looks like TypeScript content
            sourceContent = source
          } else if (fs.existsSync(source)) {
            // It's a file path - read the content
            sourceContent = fs.readFileSync(source, 'utf8')
          } else {
            // Assume it's TypeScript content
            sourceContent = source
          }
          
          const parseResult = parseTypeScript(
            sourceContent, 
            options.patterns, 
            options.includeJSDoc, 
            options.mode
          )
          results.results[key] = parseResult
          results.metadata!.successCount++
        } catch (error) {
          results.results[key] = {
            ast: {},
            interfaces: [],
            types: [],
            enums: [],
            error: error instanceof Error ? error.message : String(error)
          }
          results.metadata!.failureCount++
        }
      }
      
      results.metadata!.processingTimeMs = Date.now() - startTime
      console.log(JSON.stringify(results, null, 2))
    }
    
  } catch (error) {
    console.error(`Error in batch processing: ${error}`)
    process.exit(1)
  }
} else {
  // Single file mode (backward compatible)
  if (filePaths.length === 0) {
    console.error('Usage: parse-typescript.ts [options] <file.ts> [file2.ts ...]')
    console.error('Options:')
    console.error('  --patterns=interface,type,enum,class,function')
    console.error('  --include-jsdoc')
    console.error('  --mode=module|script')
    console.error('  --batch                      Enable batch mode (read JSON from stdin)')
    console.error('  --batch-input=<file>         Read batch input from JSON file')
    console.error('')
    console.error('Batch input format: {"sources": {"key1": "source1", "key2": "source2"}}')
    process.exit(1)
  }

  // Process multiple files
  if (filePaths.length > 1) {
    const startTime = Date.now()
    const results: BatchResult = {
      results: {},
      metadata: {
        totalFiles: filePaths.length,
        successCount: 0,
        failureCount: 0,
        processingTimeMs: 0
      }
    }
    
    for (const filePath of filePaths) {
      try {
        const source = fs.readFileSync(filePath, 'utf8')
        const result = parseTypeScript(source, options.patterns, options.includeJSDoc, options.mode)
        results.results[filePath] = result
        results.metadata!.successCount++
      } catch (error) {
        results.results[filePath] = {
          ast: {},
          interfaces: [],
          types: [],
          enums: [],
          error: error instanceof Error ? error.message : String(error)
        }
        results.metadata!.failureCount++
      }
    }
    
    results.metadata!.processingTimeMs = Date.now() - startTime
    console.log(JSON.stringify(results, null, 2))
  } else {
    // Single file processing (original behavior)
    try {
      const source = fs.readFileSync(filePaths[0], 'utf8')
      const result = parseTypeScript(source, options.patterns, options.includeJSDoc, options.mode)
      console.log(JSON.stringify(result, null, 2))
    } catch (error) {
      console.error(`Error reading file: ${error}`)
      process.exit(1)
    }
  }
}

export { parseTypeScript, ParseResult, BatchInput, BatchResult }