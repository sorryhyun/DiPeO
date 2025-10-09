/**
 * Type alias extractor for TypeScript AST
 */
import { getJSDoc } from './utils';
export function parseTypeAliases(sourceFile, includeJSDoc) {
    const types = [];
    sourceFile.getTypeAliases().forEach(typeAlias => {
        // Get the type node to preserve original syntax
        const typeNode = typeAlias.getTypeNode();
        const typeText = typeNode ? typeNode.getText() : typeAlias.getType().getText(typeAlias);
        types.push({
            name: typeAlias.getName(),
            type: typeText,
            isExported: typeAlias.isExported(),
            jsDoc: includeJSDoc ? getJSDoc(typeAlias) : undefined
        });
    });
    return types;
}
