# Fix Guide: Python Model Generation Issue

## Issue Description

The TypeScript to Python generator is producing invalid Python syntax for the `TypescriptAstNodeData.extractPatterns` field:

**Current (Invalid)**:
```python
extractPatterns: Optional[Union[("function", Literal["interface"], ...)]] = Field(default=None)
```

**Expected (Valid)**:
```python
extractPatterns: Optional[List[Literal["interface", "type", "enum", "class", "function", "const", "export"]]] = Field(default=None)
```

## Root Cause

The TypeScript type:
```typescript
extractPatterns?: ('interface' | 'type' | 'enum' | 'class' | 'function' | 'const' | 'export')[];
```

Is being incorrectly parsed due to the parentheses in the union type within the array.

## Fix Location

File: `/home/soryhyun/DiPeO/dipeo/models/scripts/generate-python.ts`

### Option 1: Quick Fix in generate-python.ts

Around line 115-124, add handling for parenthesized unions:

```typescript
// Handle parenthesized union arrays like ('a' | 'b')[]
if (ts.startsWith('(') && ts.includes(')[]')) {
    const unionContent = ts.slice(1, ts.indexOf(')'));
    const unionParts = unionContent.split('|').map(p => p.trim());
    
    // Check if all parts are string literals
    if (unionParts.every(p => /^['"][^'"]+['"]$/.test(p))) {
        this.add('typing', 'List', 'Literal');
        const literals = unionParts.map(p => p.replace(/['"]/g, '"')).join(', ');
        const T = `List[Literal[${literals}]]`;
        return save(opt ? this.optional(T) : T);
    }
}
```

### Option 2: Update TypeScript Definition

Change the TypeScript definition to avoid parentheses:

```typescript
// In diagram.ts
export interface TypescriptAstNodeData extends BaseNodeData {
  source?: string;
  extractPatterns?: Array<'interface' | 'type' | 'enum' | 'class' | 'function' | 'const' | 'export'>;
  includeJSDoc?: boolean;
  parseMode?: 'module' | 'script';
}
```

### Option 3: Use Type Alias

Define a type alias in TypeScript:

```typescript
type ExtractPattern = 'interface' | 'type' | 'enum' | 'class' | 'function' | 'const' | 'export';

export interface TypescriptAstNodeData extends BaseNodeData {
  source?: string;
  extractPatterns?: ExtractPattern[];
  includeJSDoc?: boolean;
  parseMode?: 'module' | 'script';
}
```

## Immediate Workaround

Until the generator is fixed, manually edit the generated Python file is not recommended since it will be overwritten. Instead:

1. Use Option 2 or 3 to change the TypeScript source
2. Run `make codegen` to regenerate

## Long-term Solution

The new diagram-based code generation system (Phase 2) includes proper TypeScript type parsing in the post-processors that will handle these edge cases correctly.