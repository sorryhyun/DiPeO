/**
 * Constant extractor for TypeScript AST
 */

import { SourceFile, Node } from 'ts-morph'
import type { ConstantInfo } from '@dipeo/models/codegen/ast-types'
import { getJSDoc, parseExpression } from './utils'

export function parseConstants(sourceFile: SourceFile, includeJSDoc: boolean): ConstantInfo[] {
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