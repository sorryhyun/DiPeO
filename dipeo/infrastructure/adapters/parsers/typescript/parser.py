"""TypeScript AST parser implementation."""

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from dipeo.core.base.exceptions import ServiceError

from .platform_utils import get_tsx_command, setup_github_actions_env


class TypeScriptParser:
    """TypeScript AST parser using ts-morph via Node.js subprocess."""
    
    def __init__(self, project_root: Path | None = None):
        """Initialize the TypeScript parser.
        
        Args:
            project_root: Project root directory. If not provided, uses DIPEO_BASE_DIR or cwd.
        """
        self.project_root = project_root or Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
        self.parser_script = self.project_root / 'dipeo' / 'infrastructure' / 'adapters' / 'parsers' / 'typescript' / 'ts_ast_extractor.ts'
        self._cache: dict[str, dict[str, Any]] = {}
    
    async def parse(
        self,
        source: str,
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse TypeScript source code and extract AST information.
        
        Args:
            source: The TypeScript source code to parse
            extract_patterns: List of patterns to extract (e.g., ["interface", "type", "enum"])
            options: Optional parser-specific options:
                - includeJSDoc: Whether to include JSDoc comments (default: False)
                - parseMode: 'module' or 'script' (default: 'module')
                
        Returns:
            Dictionary containing:
                - ast: The extracted AST nodes organized by pattern type
                - metadata: Additional metadata about the parsing operation
                
        Raises:
            ServiceError: If parsing fails
        """
        options = options or {}
        include_jsdoc = options.get('includeJSDoc', False)
        parse_mode = options.get('parseMode', 'module')
        
        if not source:
            raise ServiceError('No TypeScript source code provided')
        
        cache_key = hashlib.md5(
            f"{source}:{','.join(sorted(extract_patterns))}:{include_jsdoc}:{parse_mode}".encode()
        ).hexdigest()
        
        if cache_key in self._cache:
            print(f"[TypeScript Parser] Cache hit for content hash {cache_key[:8]}")
            return self._cache[cache_key]
        
        # Ensure parser script exists
        if not self.parser_script.exists():
            raise ServiceError(f'TypeScript parser script not found at {self.parser_script}')
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as tmp_file:
                tmp_file.write(source)
                tmp_file_path = tmp_file.name
            
            # Get platform-specific command
            try:
                base_cmd = get_tsx_command(self.project_root)
            except RuntimeError as e:
                raise ServiceError(str(e))
            
            # Build full command
            cmd = base_cmd + [str(self.parser_script)]
            
            if extract_patterns:
                cmd.append(f'--patterns={",".join(extract_patterns)}')
            
            if include_jsdoc:
                cmd.append('--include-jsdoc')
            
            cmd.append(f'--mode={parse_mode}')
            cmd.append(tmp_file_path)
            
            # Setup environment (handles GitHub Actions if needed)
            env = setup_github_actions_env(os.environ.copy())
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                env=env,
                timeout=30
            )
            
            os.unlink(tmp_file_path)
            
            if result.returncode != 0:
                print(f"[TypeScript Parser] Parser failed with return code {result.returncode}")
                print(f"[TypeScript Parser] Command was: {' '.join(cmd)}")
                print(f"[TypeScript Parser] Working directory: {self.project_root}")
                print(f"[TypeScript Parser] stderr: {result.stderr}")
                print(f"[TypeScript Parser] stdout: {result.stdout[:500]}...")
                # Check if this is a "command not found" error
                if "is not recognized" in result.stderr or "command not found" in result.stderr.lower():
                    print("[TypeScript Parser] ERROR: TypeScript parser command not found. Check pnpm/npx installation.")
                raise ServiceError(f'Parser failed: {result.stderr}')
            
            parsed_result = json.loads(result.stdout)

            # Check for parser errors
            if parsed_result.get('error'):
                raise ServiceError(f'Parser error: {parsed_result["error"]}')
            
            ast_data = {}
            for pattern in extract_patterns:
                if pattern == 'interface':
                    ast_data['interfaces'] = parsed_result.get('interfaces', [])
                elif pattern == 'type':
                    ast_data['types'] = parsed_result.get('types', [])
                elif pattern == 'enum':
                    ast_data['enums'] = parsed_result.get('enums', [])
                elif pattern == 'class':
                    ast_data['classes'] = parsed_result.get('classes', [])
                elif pattern == 'function':
                    ast_data['functions'] = parsed_result.get('functions', [])
                elif pattern == 'const' or pattern == 'constants':
                    ast_data['constants'] = parsed_result.get('constants', [])

            result = {
                'ast': ast_data,
                'metadata': {
                    'success': True,
                    'extractedPatterns': extract_patterns,
                    'astSummary': parsed_result.get('ast', {})
                }
            }
            
            self._cache[cache_key] = result
            print(f"[TypeScript Parser] Cached result for content hash {cache_key[:8]}")
            
            return result
            
        except subprocess.TimeoutExpired:
            # Clean up temp file if it exists
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            raise ServiceError('TypeScript parsing timed out after 30 seconds')
        except json.JSONDecodeError as e:
            # Clean up temp file if it exists
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            raise ServiceError(f'Failed to parse JSON output: {e!s}')
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_file_path' in locals():
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            raise ServiceError(f'Unexpected error during TypeScript parsing: {e!s}')
    
    def clear_cache(self):
        """Clear the in-memory AST cache."""
        self._cache.clear()
        print("[TypeScript Parser] Cache cleared")
    
    async def parse_file(self, file_path: str, extract_patterns: list[str], options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Parse a TypeScript file.
        
        Args:
            file_path: Path to the TypeScript file (relative to project root)
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Same as parse() method
            
        Raises:
            ServiceError: If file reading or parsing fails
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            raise ServiceError(f'File not found: {full_path}')
        
        try:
            with open(full_path, encoding='utf-8') as f:
                source = f.read()
            
            return await self.parse(source, extract_patterns, options)
        
        except Exception as e:
            raise ServiceError(f'Failed to read file: {e!s}')
    
    async def parse_batch(
        self,
        sources: dict[str, str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple TypeScript sources in a single operation.
        
        This method significantly reduces subprocess overhead by processing
        all sources in a single Node.js execution.
        
        Args:
            sources: Dictionary mapping keys to TypeScript source code
            extract_patterns: List of patterns to extract (e.g., ["interface", "type", "enum"])
            options: Optional parser-specific options
                
        Returns:
            Dictionary mapping each key to its parse result
                
        Raises:
            ServiceError: If batch parsing fails
        """
        options = options or {}
        include_jsdoc = options.get('includeJSDoc', False)
        parse_mode = options.get('parseMode', 'module')
        
        if not sources:
            return {}
        
        cached_results = {}
        uncached_sources = {}
        
        for key, source in sources.items():
            cache_key = hashlib.md5(
                f"{source}:{','.join(sorted(extract_patterns))}:{include_jsdoc}:{parse_mode}".encode()
            ).hexdigest()
            
            if cache_key in self._cache:
                print(f"[TypeScript Parser] Batch: Cache hit for {key} (hash {cache_key[:8]})")
                cached_results[key] = self._cache[cache_key]
            else:
                uncached_sources[key] = source
        
        if not uncached_sources:
            return cached_results
        
        print(f"[TypeScript Parser] Batch processing {len(uncached_sources)} uncached sources")
        
        # Ensure parser script exists
        if not self.parser_script.exists():
            raise ServiceError(f'TypeScript parser script not found at {self.parser_script}')
        
        try:
            # Prepare batch input
            batch_input = json.dumps({
                'sources': uncached_sources
            })
            
            # Get platform-specific command
            try:
                base_cmd = get_tsx_command(self.project_root)
            except RuntimeError as e:
                raise ServiceError(str(e))
            
            # Build full command
            cmd = base_cmd + [str(self.parser_script), '--batch']
            
            if extract_patterns:
                cmd.append(f'--patterns={",".join(extract_patterns)}')
            
            if include_jsdoc:
                cmd.append('--include-jsdoc')
            
            cmd.append(f'--mode={parse_mode}')
            
            # Setup environment (handles GitHub Actions if needed)
            env = setup_github_actions_env(os.environ.copy())
            
            result = subprocess.run(
                cmd,
                input=batch_input,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                env=env,
                timeout=60  # Increased timeout for batch processing
            )
            
            if result.returncode != 0:
                print(f"[TypeScript Parser] Batch parser failed with return code {result.returncode}")
                print(f"[TypeScript Parser] Command was: {' '.join(cmd)}")
                print(f"[TypeScript Parser] Working directory: {self.project_root}")
                print(f"[TypeScript Parser] stderr: {result.stderr}")
                print(f"[TypeScript Parser] stdout: {result.stdout[:500]}...")
                # Check if this is a "command not found" error
                if "is not recognized" in result.stderr or "command not found" in result.stderr.lower():
                    print("[TypeScript Parser] ERROR: TypeScript parser command not found. Check pnpm/npx installation.")
                raise ServiceError(f'Batch parser failed: {result.stderr}')
            
            # Parse the JSON output
            batch_result = json.loads(result.stdout)
            
            # Process and cache results
            results = {}
            for key, parse_result in batch_result.get('results', {}).items():
                if parse_result.get('error'):
                    print(f"[TypeScript Parser] Error parsing {key}: {parse_result['error']}")
                    continue
                
                # Extract AST data
                ast_data = {}
                for pattern in extract_patterns:
                    if pattern == 'interface':
                        ast_data['interfaces'] = parse_result.get('interfaces', [])
                    elif pattern == 'type':
                        ast_data['types'] = parse_result.get('types', [])
                    elif pattern == 'enum':
                        ast_data['enums'] = parse_result.get('enums', [])
                    elif pattern == 'class':
                        ast_data['classes'] = parse_result.get('classes', [])
                    elif pattern == 'function':
                        ast_data['functions'] = parse_result.get('functions', [])
                    elif pattern == 'const' or pattern == 'constants':
                        ast_data['constants'] = parse_result.get('constants', [])
                
                formatted_result = {
                    'ast': ast_data,
                    'metadata': {
                        'success': True,
                        'extractedPatterns': extract_patterns,
                        'astSummary': parse_result.get('ast', {})
                    }
                }
                
                # Cache the result
                source = uncached_sources[key]
                cache_key = hashlib.md5(
                    f"{source}:{','.join(sorted(extract_patterns))}:{include_jsdoc}:{parse_mode}".encode()
                ).hexdigest()
                self._cache[cache_key] = formatted_result
                
                results[key] = formatted_result
            
            # Combine with cached results
            results.update(cached_results)
            
            # Log batch processing statistics
            if 'metadata' in batch_result:
                meta = batch_result['metadata']
                print(f"[TypeScript Parser] Batch completed: {meta['successCount']}/{meta['totalFiles']} successful in {meta['processingTimeMs']}ms")
            
            return results
            
        except subprocess.TimeoutExpired:
            raise ServiceError('Batch TypeScript parsing timed out after 60 seconds')
        except json.JSONDecodeError as e:
            raise ServiceError(f'Failed to parse batch JSON output: {e!s}')
        except Exception as e:
            raise ServiceError(f'Unexpected error during batch TypeScript parsing: {e!s}')
    
    async def parse_files_batch(
        self,
        file_paths: list[str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple TypeScript files in a single operation.
        
        Args:
            file_paths: List of file paths relative to project root
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Dictionary mapping file paths to parse results
            
        Raises:
            ServiceError: If file reading or parsing fails
        """
        sources = {}
        
        for file_path in file_paths:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                print(f"[TypeScript Parser] Warning: File not found: {full_path}")
                continue
            
            try:
                with open(full_path, encoding='utf-8') as f:
                    sources[file_path] = f.read()
            except Exception as e:
                print(f"[TypeScript Parser] Warning: Failed to read file {file_path}: {e!s}")
                continue
        
        if not sources:
            return {}
        
        return await self.parse_batch(sources, extract_patterns, options)