/**
 * Utility functions for TypeScript AST extraction
 */

import { Node, SourceFile } from 'ts-morph'

/**
 * Map to store resolved const values for reference resolution
 */
let constValueMap: Map<string, any> = new Map()

/**
 * Set the const value map for a parsing session
 * @param map The map of const names to their resolved values
 */
export function setConstValueMap(map: Map<string, any>): void {
  constValueMap = map
}

/**
 * Clear the const value map after parsing
 */
export function clearConstValueMap(): void {
  constValueMap.clear()
}

/**
 * Resolve a const reference by looking it up in the const value map
 * @param identifier The identifier to resolve
 * @returns The resolved value or the identifier itself if not found
 */
export function resolveConstReference(identifier: string): any {
  if (constValueMap.has(identifier)) {
    return constValueMap.get(identifier)
  }
  return identifier
}

/**
 * Resolve an enum member value from a property access expression
 * @param node PropertyAccessExpression node (e.g., HookTriggerMode.NONE)
 * @returns The enum member value or null if not found
 */
export function resolveEnumValue(node: Node): any {
  if (!Node.isPropertyAccessExpression(node)) {
    return null
  }

  const nodeText = node.getText()
  console.error(`[DEBUG] Attempting to resolve enum value: ${nodeText}`)

  try {
    // Get the type of the property access expression
    const type = node.getType()

    // Check if it's an enum type by checking if it has a literal value
    if (type.isLiteral()) {
      const literalValue = type.getLiteralValue()
      if (literalValue !== undefined) {
        console.error(`[DEBUG] Resolved ${nodeText} to literal: ${literalValue}`)
        return literalValue
      }
    }

    // Alternative approach: Try to get the constant value directly
    const symbol = node.getSymbol()
    if (symbol) {
      const valueDeclaration = symbol.getValueDeclaration()
      if (valueDeclaration && Node.isEnumMember(valueDeclaration)) {
        const initializer = valueDeclaration.getInitializer()
        if (initializer) {
          // Parse the initializer to get the value
          if (Node.isStringLiteral(initializer)) {
            const value = initializer.getLiteralValue()
            console.error(`[DEBUG] Resolved ${nodeText} via enum member to: ${value}`)
            return value
          }
          if (Node.isNumericLiteral(initializer)) {
            const value = initializer.getLiteralValue()
            console.error(`[DEBUG] Resolved ${nodeText} via enum member to: ${value}`)
            return value
          }
        }
      }
    }
  } catch (e) {
    console.error(`[DEBUG] Error resolving ${nodeText}: ${e}`)
    // If resolution fails, return null to fall back to text representation
    return null
  }

  console.error(`[DEBUG] Could not resolve ${nodeText}, returning null`)
  return null
}

export function getJSDoc(node: Node): string | undefined {
  // Check if the node has JSDoc support
  if ('getJsDocs' in node && typeof node.getJsDocs === 'function') {
    const jsDocs = (node as any).getJsDocs()
    if (jsDocs.length > 0) {
      return jsDocs[0].getDescription().trim()
    }
  }
  return undefined
}

export function parseExpression(node: Node): any {
  // Object literal
  if (Node.isObjectLiteralExpression(node)) {
    return parseObjectLiteral(node)
  }

  // Array literal
  if (Node.isArrayLiteralExpression(node)) {
    return node.getElements().map(elem => parseExpression(elem))
  }

  // String literal
  if (Node.isStringLiteral(node)) {
    return node.getLiteralValue()
  }

  // Numeric literal
  if (Node.isNumericLiteral(node)) {
    return node.getLiteralValue()
  }

  // Boolean literal
  if (Node.isTrueLiteral(node)) {
    return true
  }
  if (Node.isFalseLiteral(node)) {
    return false
  }

  // Null literal
  if (Node.isNullLiteral(node)) {
    return null
  }

  // Property access expression (e.g., HookTriggerMode.NONE, NodeType.START)
  if (Node.isPropertyAccessExpression(node)) {
    const enumValue = resolveEnumValue(node)
    if (enumValue !== null) {
      return enumValue
    }
    // If we can't resolve it, fall through to return the text
  }

  // Identifier (e.g., undefined, const references)
  if (Node.isIdentifier(node)) {
    const text = node.getText()
    if (text === 'undefined') {
      return undefined
    }
    // Try to resolve const reference
    const resolved = resolveConstReference(text)
    // If resolved to something other than the identifier itself, return the resolved value
    if (resolved !== text) {
      return resolved
    }
    // Return identifier name for other cases
    return text
  }

  // For other node types, return the text representation
  return node.getText()
}

function parseObjectLiteral(node: Node): any {
  const result: any = {}

  // Use ts-morph's proper API to get object literal properties
  if (Node.isObjectLiteralExpression(node)) {
    const objLiteral = node

    objLiteral.getProperties().forEach(prop => {
      if (Node.isPropertyAssignment(prop)) {
        const name = prop.getName()
        const initializer = prop.getInitializer()

        if (initializer) {
          result[name] = parseExpression(initializer)
        } else {
          result[name] = undefined
        }
      } else if (Node.isShorthandPropertyAssignment(prop)) {
        const name = prop.getName()
        result[name] = name // Shorthand properties
      }
    })
  }

  return result
}
