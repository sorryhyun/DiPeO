/**
 * Interface extractor for TypeScript AST
 */

import { SourceFile } from 'ts-morph'
import type { InterfaceInfo, PropertyInfo } from '@dipeo/models/codegen/ast-types'
import { getJSDoc } from './utils'

export function parseInterfaces(sourceFile: SourceFile, includeJSDoc: boolean): InterfaceInfo[] {
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
