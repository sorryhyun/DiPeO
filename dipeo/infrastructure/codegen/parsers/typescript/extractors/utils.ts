/**
 * Utility functions for TypeScript AST extraction
 */

import { Node, SourceFile } from 'ts-morph'

/**
 * Map to store resolved const values for reference resolution
 */
let constValueMap: Map<string, any> = new Map()

/**
 * Map to store enum values for enum reference resolution
 * Structure: Map<"EnumName.MemberName", value>
 */
let enumValueMap: Map<string, any> = new Map()

/**
 * Set the const value map for a parsing session
 * @param map The map of const names to their resolved values
 */
export function setConstValueMap(map: Map<string, any>): void {
  constValueMap = map
}

/**
 * Set the enum value map for a parsing session
 * @param map The map of enum member references to their values
 */
export function setEnumValueMap(map: Map<string, any>): void {
  enumValueMap = map
}

/**
 * Clear the const value map after parsing
 */
export function clearConstValueMap(): void {
  constValueMap.clear()
}

/**
 * Clear the enum value map after parsing
 */
export function clearEnumValueMap(): void {
  enumValueMap.clear()
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

  // First, try to look up in the enum value map (for same-file enums)
  if (enumValueMap.has(nodeText)) {
    const value = enumValueMap.get(nodeText)
    return value
  }

  // For imported enums, use symbol-based resolution
  try {
    const symbol = node.getSymbol()
    if (symbol) {
      const valueDeclaration = symbol.getValueDeclaration()

      // Check if it's an enum member
      if (valueDeclaration && Node.isEnumMember(valueDeclaration)) {
        const initializer = valueDeclaration.getInitializer()
        if (initializer) {
          // Parse the initializer to get the value
          if (Node.isStringLiteral(initializer)) {
            return initializer.getLiteralValue()
          }
          if (Node.isNumericLiteral(initializer)) {
            return initializer.getLiteralValue()
          }
        } else {
          // No initializer means it's auto-numbered - get the index
          const enumDecl = valueDeclaration.getParent()
          if (Node.isEnumDeclaration(enumDecl)) {
            const members = enumDecl.getMembers()
            const index = members.indexOf(valueDeclaration as any)
            if (index >= 0) {
              return index
            }
          }
        }
      }
    }

    // Fallback: Try type-based resolution for literal types
    const type = node.getType()
    if (type.isLiteral()) {
      const literalValue = type.getLiteralValue()
      if (literalValue !== undefined) {
        return literalValue
      }
    }
  } catch (e) {
    // If resolution fails, return null
    return null
  }

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
    const result: any[] = []
    for (const elem of node.getElements()) {
      if (Node.isSpreadElement(elem)) {
        // Handle spread operator
        const spreadExpression = elem.getExpression()
        const spreadValue = parseExpression(spreadExpression)

        // If the spread value is an array, flatten it
        if (Array.isArray(spreadValue)) {
          result.push(...spreadValue)
        } else {
          // If it's not an array, just push it as-is (might be a non-evaluated expression)
          result.push(spreadValue)
        }
      } else {
        // Regular element
        result.push(parseExpression(elem))
      }
    }
    return result
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

  // Arrow function (e.g., () => {...} or (x) => x + 1)
  if (Node.isArrowFunction(node)) {
    const arrowFunc = node
    const body = arrowFunc.getBody()

    // Create a callable function that evaluates the arrow function body
    const parameters = arrowFunc.getParameters().map(p => p.getName())

    // Return a function that can be called later
    return (...args: any[]) => {
      // Build a parameter map
      const paramMap = new Map<string, any>()
      parameters.forEach((param, index) => {
        paramMap.set(param, args[index])
      })

      // Merge param map into const map temporarily
      const originalConstMap = new Map(constValueMap)
      paramMap.forEach((value, key) => {
        constValueMap.set(key, value)
      })

      try {
        // If the body is a block, look for return statement
        if (Node.isBlock(body)) {
          const statements = body.getStatements()
          for (const stmt of statements) {
            if (Node.isReturnStatement(stmt)) {
              const returnExpr = stmt.getExpression()
              if (returnExpr) {
                const result = parseExpression(returnExpr)
                // Restore original const map
                constValueMap.clear()
                originalConstMap.forEach((value, key) => constValueMap.set(key, value))
                return result
              }
            }
          }
          // If no return statement, return undefined
          constValueMap.clear()
          originalConstMap.forEach((value, key) => constValueMap.set(key, value))
          return undefined
        } else {
          // Concise arrow function: expression is the body
          const result = parseExpression(body)
          // Restore original const map
          constValueMap.clear()
          originalConstMap.forEach((value, key) => constValueMap.set(key, value))
          return result
        }
      } catch (e) {
        // Restore original const map on error
        constValueMap.clear()
        originalConstMap.forEach((value, key) => constValueMap.set(key, value))
        throw e
      }
    }
  }

  // Call expression (e.g., promptWithFileField())
  if (Node.isCallExpression(node)) {
    const callExpr = node
    const expression = callExpr.getExpression()

    // Get function name
    let functionName: string | null = null
    if (Node.isIdentifier(expression)) {
      functionName = expression.getText()
    } else if (Node.isPropertyAccessExpression(expression)) {
      functionName = expression.getText()
    }

    if (functionName) {
      // Try to resolve the function from const map
      const func = resolveConstReference(functionName)

      // If the function is resolved and is actually a function, call it
      if (typeof func === 'function') {
        try {
          // Parse arguments
          const args = callExpr.getArguments().map(arg => parseExpression(arg))
          // Call the function with arguments
          return func(...args)
        } catch (e) {
          // If function call fails, return the call text
          return node.getText()
        }
      } else if (func && typeof func === 'object') {
        // If it resolved to an object/array (pre-computed value), return it
        return func
      }
    }

    // If we can't resolve the function, return the call text
    return node.getText()
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
      } else if (Node.isSpreadAssignment(prop)) {
        // Handle spread operator in object literal
        const spreadExpression = prop.getExpression()
        const spreadValue = parseExpression(spreadExpression)

        // If the spread value is an object, merge it
        if (spreadValue && typeof spreadValue === 'object' && !Array.isArray(spreadValue)) {
          Object.assign(result, spreadValue)
        }
      }
    })
  }

  return result
}
