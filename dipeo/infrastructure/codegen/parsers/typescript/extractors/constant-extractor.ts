/**
 * Constant extractor for TypeScript AST
 */

import { SourceFile, Node } from 'ts-morph'
import type { ConstantInfo } from '@dipeo/models/codegen/ast-types'
import { getJSDoc, parseExpression, setConstValueMap, clearConstValueMap } from './utils'

export function parseConstants(sourceFile: SourceFile, includeJSDoc: boolean): ConstantInfo[] {
  const constants: ConstantInfo[] = []
  const constMap = new Map<string, any>()

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

  // Clear the const map after parsing
  clearConstValueMap()

  return constants
}
