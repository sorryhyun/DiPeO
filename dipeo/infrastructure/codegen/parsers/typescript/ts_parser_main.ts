#!/usr/bin/env tsx
/**
 * Main TypeScript parser orchestrator
 * Uses modular extractors to parse TypeScript source code
 */

import { Project, SourceFile } from 'ts-morph'
import * as fs from 'fs'
import {
  ParseResult,
  BatchInput,
  BatchResult,
  parseInterfaces,
  parseTypeAliases,
  parseEnums,
  parseClasses,
  parseFunctions,
  parseConstants
} from './extractors'

/**
 * Main parsing function that orchestrates all extractors
 */
function parseTypeScript(
  source: string,
  extractPatterns: string[],
  includeJSDoc: boolean = false,
  mode: 'module' | 'script' = 'module'
): ParseResult {
  try {
    const project = new Project({
      useInMemoryFileSystem: true,
      compilerOptions: {
        allowJs: true,
        strict: false,
        skipLibCheck: true,
        noEmit: true
      }
    })
    
    const fileName = mode === 'module' ? 'temp.ts' : 'temp-script.ts'
    const sourceFile = project.createSourceFile(fileName, source)
    
    const result: ParseResult = {
      ast: {},
      interfaces: [],
      types: [],
      enums: []
    }
    
    // Extract based on requested patterns using modular extractors
    if (extractPatterns.includes('interface')) {
      result.interfaces = parseInterfaces(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('type')) {
      result.types = parseTypeAliases(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('enum')) {
      result.enums = parseEnums(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('class')) {
      result.classes = parseClasses(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('function')) {
      result.functions = parseFunctions(sourceFile, includeJSDoc)
    }
    
    if (extractPatterns.includes('const') || extractPatterns.includes('constants')) {
      result.constants = parseConstants(sourceFile, includeJSDoc)
    }
    
    // Simple AST representation (for debugging/visualization)
    result.ast = {
      kind: sourceFile.getKindName(),
      childCount: sourceFile.getChildren().length,
      hasInterfaces: result.interfaces.length > 0,
      hasTypes: result.types.length > 0,
      hasEnums: result.enums.length > 0,
      hasClasses: (result.classes?.length || 0) > 0,
      hasFunctions: (result.functions?.length || 0) > 0,
      hasConstants: (result.constants?.length || 0) > 0
    }
    
    return result
  } catch (error) {
    return {
      ast: {},
      interfaces: [],
      types: [],
      enums: [],
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

/**
 * Process batch input
 */
function processBatchInput(
  input: BatchInput,
  options: { patterns: string[], includeJSDoc: boolean, mode: 'module' | 'script' }
): BatchResult {
  const startTime = Date.now()
  const results: BatchResult = {
    results: {},
    metadata: {
      totalFiles: 0,
      successCount: 0,
      failureCount: 0,
      processingTimeMs: 0
    }
  }
  
  // Process each source
  for (const [key, source] of Object.entries(input.sources)) {
    results.metadata!.totalFiles++
    
    try {
      // Check if source is a file path or TypeScript content
      let sourceContent: string
      if (source.includes('\n') || source.includes('import') || source.includes('export')) {
        // Looks like TypeScript content
        sourceContent = source
      } else if (fs.existsSync(source)) {
        // It's a file path - read the content
        sourceContent = fs.readFileSync(source, 'utf8')
      } else {
        // Assume it's TypeScript content
        sourceContent = source
      }
      
      const parseResult = parseTypeScript(
        sourceContent, 
        options.patterns, 
        options.includeJSDoc, 
        options.mode
      )
      results.results[key] = parseResult
      results.metadata!.successCount++
    } catch (error) {
      results.results[key] = {
        ast: {},
        interfaces: [],
        types: [],
        enums: [],
        error: error instanceof Error ? error.message : String(error)
      }
      results.metadata!.failureCount++
    }
  }
  
  results.metadata!.processingTimeMs = Date.now() - startTime
  return results
}

// Command line interface
const args = process.argv.slice(2)

// Extract file paths and options
const filePaths: string[] = []
const options = args.reduce((acc, arg) => {
  if (!arg.startsWith('--')) {
    filePaths.push(arg)
    return acc
  }
  if (arg.startsWith('--patterns=')) {
    acc.patterns = arg.substring(11).split(',')
  } else if (arg === '--include-jsdoc') {
    acc.includeJSDoc = true
  } else if (arg.startsWith('--mode=')) {
    acc.mode = arg.substring(7) as 'module' | 'script'
  } else if (arg === '--batch' || arg === '--batch-mode') {
    acc.batchMode = true
  } else if (arg.startsWith('--batch-input=')) {
    acc.batchInputFile = arg.substring(14)
  }
  return acc
}, {
  patterns: ['interface', 'type', 'enum'],
  includeJSDoc: false,
  mode: 'module' as 'module' | 'script',
  batchMode: false,
  batchInputFile: undefined as string | undefined
})

// Process batch input if provided
if (options.batchMode || options.batchInputFile) {
  try {
    let batchInput: BatchInput
    
    if (options.batchInputFile) {
      // Read batch input from JSON file
      const inputData = fs.readFileSync(options.batchInputFile, 'utf8')
      batchInput = JSON.parse(inputData)
      const result = processBatchInput(batchInput, options)
      console.log(JSON.stringify(result, null, 2))
    } else if (process.stdin.isTTY === false) {
      // Read from stdin if not a TTY
      const chunks: Buffer[] = []
      process.stdin.on('data', (chunk) => chunks.push(chunk))
      process.stdin.on('end', () => {
        try {
          const inputData = Buffer.concat(chunks).toString()
          batchInput = JSON.parse(inputData)
          const result = processBatchInput(batchInput, options)
          console.log(JSON.stringify(result, null, 2))
        } catch (error) {
          console.error(`Error parsing batch input: ${error}`)
          process.exit(1)
        }
      })
      // Exit here to wait for stdin
      process.stdin.resume()
    } else {
      console.error('Batch mode requires either --batch-input=<file> or input via stdin')
      process.exit(1)
    }
  } catch (error) {
    console.error(`Error in batch processing: ${error}`)
    process.exit(1)
  }
} else {
  // Single file mode (backward compatible)
  if (filePaths.length === 0) {
    console.error('Usage: ts_parser_main.ts [options] <file.ts> [file2.ts ...]')
    console.error('Options:')
    console.error('  --patterns=interface,type,enum,class,function')
    console.error('  --include-jsdoc')
    console.error('  --mode=module|script')
    console.error('  --batch                      Enable batch mode (read JSON from stdin)')
    console.error('  --batch-input=<file>         Read batch input from JSON file')
    console.error('')
    console.error('Batch input format: {"sources": {"key1": "source1", "key2": "source2"}}')
    process.exit(1)
  }

  // Process multiple files
  if (filePaths.length > 1) {
    const startTime = Date.now()
    const results: BatchResult = {
      results: {},
      metadata: {
        totalFiles: filePaths.length,
        successCount: 0,
        failureCount: 0,
        processingTimeMs: 0
      }
    }
    
    for (const filePath of filePaths) {
      try {
        const source = fs.readFileSync(filePath, 'utf8')
        const result = parseTypeScript(source, options.patterns, options.includeJSDoc, options.mode)
        results.results[filePath] = result
        results.metadata!.successCount++
      } catch (error) {
        results.results[filePath] = {
          ast: {},
          interfaces: [],
          types: [],
          enums: [],
          error: error instanceof Error ? error.message : String(error)
        }
        results.metadata!.failureCount++
      }
    }
    
    results.metadata!.processingTimeMs = Date.now() - startTime
    console.log(JSON.stringify(results, null, 2))
  } else {
    // Single file processing (original behavior)
    try {
      const source = fs.readFileSync(filePaths[0], 'utf8')
      const result = parseTypeScript(source, options.patterns, options.includeJSDoc, options.mode)
      console.log(JSON.stringify(result, null, 2))
    } catch (error) {
      console.error(`Error reading file: ${error}`)
      process.exit(1)
    }
  }
}