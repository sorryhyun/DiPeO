/**
 * Function extractor for TypeScript AST
 */

import { SourceFile } from 'ts-morph'
import type { FunctionInfo, ParameterInfo } from '@dipeo/models/src/codegen/ast-types'
import { getJSDoc } from './utils'

export function parseFunctions(sourceFile: SourceFile, includeJSDoc: boolean): FunctionInfo[] {
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
