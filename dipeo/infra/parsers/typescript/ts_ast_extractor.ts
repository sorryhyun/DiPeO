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

// Command line interface
const args = process.argv.slice(2)

// Extract file path and options
let filePath: string | undefined
const options = args.reduce((acc, arg) => {
  if (!arg.startsWith('--')) {
    filePath = arg
    return acc
  }
  if (arg.startsWith('--patterns=')) {
    acc.patterns = arg.substring(11).split(',')
  } else if (arg === '--include-jsdoc') {
    acc.includeJSDoc = true
  } else if (arg.startsWith('--mode=')) {
    acc.mode = arg.substring(7) as 'module' | 'script'
  }
  return acc
}, {
  patterns: ['interface', 'type', 'enum'],
  includeJSDoc: false,
  mode: 'module' as 'module' | 'script'
})

// Validate arguments
if (!filePath) {
  console.error('Usage: parse-typescript.ts [options] <file.ts>')
  console.error('Options:')
  console.error('  --patterns=interface,type,enum,class,function')
  console.error('  --include-jsdoc')
  console.error('  --mode=module|script')
  process.exit(1)
}

// Read source code from file
try {
  const source = fs.readFileSync(filePath, 'utf8')
  const result = parseTypeScript(source, options.patterns, options.includeJSDoc, options.mode)
  console.log(JSON.stringify(result, null, 2))
} catch (error) {
  console.error(`Error reading file: ${error}`)
  process.exit(1)
}

export { parseTypeScript, ParseResult }