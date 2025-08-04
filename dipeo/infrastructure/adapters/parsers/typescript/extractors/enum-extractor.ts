/**
 * Enum extractor for TypeScript AST
 */

import { SourceFile } from 'ts-morph'
import type { EnumInfo } from '@dipeo/domain-models/parsers/ast-types'
import { getJSDoc } from './utils'

export function parseEnums(sourceFile: SourceFile, includeJSDoc: boolean): EnumInfo[] {
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