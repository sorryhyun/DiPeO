/**
 * Constant extractor for TypeScript AST
 */
import { getJSDoc, parseExpression, setConstValueMap, clearConstValueMap } from './utils';
export function parseConstants(sourceFile, includeJSDoc) {
    const constants = [];
    const constMap = new Map();
    // First pass: collect all const declarations without resolving references
    const constDeclarations = [];
    sourceFile.getVariableDeclarations().forEach(varDecl => {
        // Only process const declarations
        const statement = varDecl.getVariableStatement();
        if (!statement || statement.getDeclarationKind() !== 'const') {
            return;
        }
        // Check if it's exported (we'll track this but parse all consts)
        const isExported = statement.isExported();
        const name = varDecl.getName();
        const type = varDecl.getType().getText(varDecl);
        const initializer = varDecl.getInitializer();
        constDeclarations.push({
            name,
            type,
            initializer,
            varDecl,
            isExported
        });
    });
    // Process declarations in order, building up the const map
    // This allows later consts to reference earlier ones
    constDeclarations.forEach(({ name, type, initializer, varDecl, isExported }) => {
        let value = undefined;
        // Set the current const map for resolution
        setConstValueMap(constMap);
        if (initializer) {
            try {
                // Parse the expression with const resolution enabled
                value = parseExpression(initializer);
            }
            catch (e) {
                // If parsing fails, store the text representation
                value = initializer.getText();
            }
        }
        // Add this const's value to the map for future references
        constMap.set(name, value);
        constants.push({
            name,
            type,
            value,
            isExported: isExported || false,
            jsDoc: includeJSDoc ? getJSDoc(varDecl) : undefined
        });
    });
    // Clear the const map after parsing
    clearConstValueMap();
    return constants;
}
