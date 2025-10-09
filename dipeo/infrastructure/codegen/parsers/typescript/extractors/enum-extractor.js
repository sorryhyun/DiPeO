/**
 * Enum extractor for TypeScript AST
 */
import { getJSDoc } from './utils';
export function parseEnums(sourceFile, includeJSDoc) {
    const enums = [];
    sourceFile.getEnums().forEach(enumDecl => {
        const members = enumDecl.getMembers().map(member => ({
            name: member.getName(),
            value: member.getValue()
        }));
        enums.push({
            name: enumDecl.getName(),
            members,
            isExported: enumDecl.isExported(),
            jsDoc: includeJSDoc ? getJSDoc(enumDecl) : undefined
        });
    });
    return enums;
}
