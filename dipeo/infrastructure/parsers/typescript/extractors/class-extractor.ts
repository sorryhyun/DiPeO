/**
 * Class extractor for TypeScript AST
 */

import { SourceFile } from 'ts-morph'
import type { ClassInfo, PropertyInfo, MethodInfo, ParameterInfo } from '@dipeo/models/codegen/ast-types'
import { getJSDoc } from './utils'

export function parseClasses(sourceFile: SourceFile, includeJSDoc: boolean): ClassInfo[] {
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