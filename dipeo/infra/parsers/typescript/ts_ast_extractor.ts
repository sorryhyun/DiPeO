#!/usr/bin/env tsx
/**
 * TypeScript AST parser using ts-morph
 * Parses TypeScript source code and extracts interfaces, types, enums, etc.
 */

import { Project, SourceFile, Node } from 'ts-morph'

interface ParseResult {
  ast: any
  interfaces: InterfaceInfo[]
  types: TypeAliasInfo[]
  enums: EnumInfo[]
  classes?: ClassInfo[]
  functions?: FunctionInfo[]
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
      properties.push({
        name: prop.getName(),
        type: prop.getType().getText(prop),
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
    types.push({
      name: typeAlias.getName(),
      type: typeAlias.getType().getText(typeAlias),
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
      properties.push({
        name: prop.getName(),
        type: prop.getType().getText(prop),
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
    
    // Simple AST representation (for debugging/visualization)
    result.ast = {
      kind: sourceFile.getKindName(),
      childCount: sourceFile.getChildren().length,
      hasInterfaces: result.interfaces.length > 0,
      hasTypes: result.types.length > 0,
      hasEnums: result.enums.length > 0,
      hasClasses: (result.classes?.length || 0) > 0,
      hasFunctions: (result.functions?.length || 0) > 0
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

if (args.length === 0) {
  console.error('Usage: parse-typescript.ts <source-code> [options]')
  console.error('Options:')
  console.error('  --patterns=interface,type,enum,class,function')
  console.error('  --include-jsdoc')
  console.error('  --mode=module|script')
  process.exit(1)
}

const source = args[0]
const options = args.slice(1).reduce((acc, arg) => {
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

const result = parseTypeScript(source, options.patterns, options.includeJSDoc, options.mode)
console.log(JSON.stringify(result, null, 2))

export { parseTypeScript, ParseResult }