/**
 * Interface extractor for TypeScript AST
 */
import { getJSDoc } from './utils';
export function parseInterfaces(sourceFile, includeJSDoc) {
    const interfaces = [];
    sourceFile.getInterfaces().forEach(interfaceDecl => {
        const properties = [];
        interfaceDecl.getProperties().forEach(prop => {
            // Get the type node to preserve original syntax (e.g., DomainNode[] instead of resolved type)
            const typeNode = prop.getTypeNode();
            const typeText = typeNode ? typeNode.getText() : prop.getType().getText(prop);
            properties.push({
                name: prop.getName(),
                type: typeText,
                optional: prop.hasQuestionToken(),
                readonly: prop.isReadonly(),
                jsDoc: includeJSDoc ? getJSDoc(prop) : undefined
            });
        });
        interfaces.push({
            name: interfaceDecl.getName(),
            properties,
            extends: interfaceDecl.getExtends().map(e => e.getText()),
            isExported: interfaceDecl.isExported(),
            jsDoc: includeJSDoc ? getJSDoc(interfaceDecl) : undefined
        });
    });
    return interfaces;
}
