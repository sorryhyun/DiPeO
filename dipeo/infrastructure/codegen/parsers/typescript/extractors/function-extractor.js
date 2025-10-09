/**
 * Function extractor for TypeScript AST
 */
import { getJSDoc } from './utils';
export function parseFunctions(sourceFile, includeJSDoc) {
    const functions = [];
    sourceFile.getFunctions().forEach(func => {
        const parameters = func.getParameters().map(param => ({
            name: param.getName(),
            type: param.getType().getText(param),
            optional: param.isOptional(),
            defaultValue: param.getInitializer()?.getText()
        }));
        functions.push({
            name: func.getName() || 'Anonymous',
            parameters,
            returnType: func.getReturnType().getText(func),
            isAsync: func.isAsync(),
            isExported: func.isExported(),
            jsDoc: includeJSDoc ? getJSDoc(func) : undefined
        });
    });
    return functions;
}
