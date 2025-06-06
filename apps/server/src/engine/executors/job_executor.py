"""
Job node executor - handles safe code execution and stateless operations
"""

from typing import Dict, Any, TYPE_CHECKING
import time
import logging
import json
import subprocess
import tempfile
import os

if TYPE_CHECKING:
    from ..engine import ExecutionContext

from .base_executor import BaseExecutor, ExecutorResult
from .utils import (
    get_input_values,
    substitute_variables
)
from .validator import (
    ValidationResult,
    validate_required_fields,
    validate_enum_field,
    validate_dangerous_code
)

logger = logging.getLogger(__name__)


class JobExecutor(BaseExecutor):
    """
    Job node executor that runs safe code execution in a sandboxed environment.
    Supports multiple languages with appropriate sandboxing.
    """
    
    SUPPORTED_LANGUAGES = ["python", "javascript", "bash"]
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate job node configuration"""
        properties = node.get("properties", {})
        
        # Validate required fields
        field_errors = validate_required_fields(
            properties, 
            ["code"],
            {"code": "Code"}
        )
        
        # Validate language enum
        language_error = validate_enum_field(
            properties,
            "language",
            self.SUPPORTED_LANGUAGES,
            case_sensitive=True
        )
        
        # Check for dangerous code patterns
        code = properties.get("code", "")
        language = properties.get("language", "python")
        code_errors, code_warnings = [], []
        
        if code and language in self.SUPPORTED_LANGUAGES:
            # Use strict=True for bash (errors), strict=False for others (warnings)
            strict = language == "bash"
            code_errors, code_warnings = validate_dangerous_code(code, language, strict=strict)
        
        # Combine all errors and warnings
        all_errors = field_errors + ([language_error] if language_error else []) + code_errors
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=code_warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute job node code in a safe environment"""
        start_time = time.time()
        
        properties = node.get("properties", {})
        code = properties.get("code", "")
        language = properties.get("language", "python")
        timeout = properties.get("timeout", 30)  # Default 30 seconds timeout
        
        # Get input values
        inputs = get_input_values(node, context)
        
        # Substitute variables in code
        code = substitute_variables(code, inputs)
        
        try:
            if language == "python":
                result = await self._execute_python(code, inputs, timeout)
            elif language == "javascript":
                result = await self._execute_javascript(code, inputs, timeout)
            elif language == "bash":
                result = await self._execute_bash(code, inputs, timeout)
            else:
                raise ValueError(f"Unsupported language: {language}")
            
            execution_time = time.time() - start_time
            
            return ExecutorResult(
                output=result,
                metadata={
                    "language": language,
                    "executionTime": execution_time,
                    "inputKeys": list(inputs.keys()),
                    "codeLength": len(code)
                },
                execution_time=execution_time
            )
        
        except Exception as e:
            return ExecutorResult(
                output=None,
                error=f"Job execution failed: {str(e)}",
                metadata={
                    "language": language,
                    "error": str(e)
                },
                execution_time=time.time() - start_time
            )
    
    async def _execute_python(self, code: str, inputs: Dict[str, Any], timeout: int) -> Any:
        """Execute Python code in a sandboxed environment"""
        # Create a restricted execution environment
        safe_globals = {
            "__builtins__": {
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "print": print,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "type": type,
                "json": json,
            }
        }
        
        # Add inputs to the execution context
        safe_locals = {"inputs": inputs, "result": None}
        
        # Wrap code to capture result
        wrapped_code = f"""
{code}

# Capture the last expression or 'result' variable
if 'result' not in locals():
    result = None
"""
        
        try:
            # Execute with timeout using subprocess for better isolation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Write execution script
                f.write(f"""
import json
import sys

inputs = {json.dumps(inputs)}

{code}

# Output result as JSON
if 'result' in locals():
    print(json.dumps(result))
else:
    print(json.dumps(None))
""")
                f.flush()
                
                # Execute in subprocess with timeout
                result = subprocess.run(
                    ["python", f.name],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                # Clean up
                os.unlink(f.name)
                
                if result.returncode != 0:
                    raise RuntimeError(f"Python execution failed: {result.stderr}")
                
                # Parse output
                output = result.stdout.strip()
                if output:
                    return json.loads(output)
                return None
                
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Python execution timed out after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Python execution error: {str(e)}")
    
    async def _execute_javascript(self, code: str, inputs: Dict[str, Any], timeout: int) -> Any:
        """Execute JavaScript code using Node.js"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                # Write execution script
                f.write(f"""
                    const inputs = {json.dumps(inputs)};
                    
                    {code}
                    
                    // Output result as JSON
                    if (typeof result !== 'undefined') {{
                        console.log(JSON.stringify(result));
                    }} else {{
                        console.log(JSON.stringify(null));
                    }}
                    """)
                f.flush()
                
                # Execute in subprocess with timeout
                result = subprocess.run(
                    ["node", f.name],
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                # Clean up
                os.unlink(f.name)
                
                if result.returncode != 0:
                    raise RuntimeError(f"JavaScript execution failed: {result.stderr}")
                
                # Parse output
                output = result.stdout.strip()
                if output:
                    return json.loads(output)
                return None
                
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"JavaScript execution timed out after {timeout} seconds")
        except FileNotFoundError:
            raise RuntimeError("Node.js not found. Please install Node.js to execute JavaScript code.")
        except Exception as e:
            raise RuntimeError(f"JavaScript execution error: {str(e)}")
    
    async def _execute_bash(self, code: str, inputs: Dict[str, Any], timeout: int) -> Any:
        """Execute Bash code with restrictions"""
        try:
            # Export inputs as environment variables
            env = os.environ.copy()
            for key, value in inputs.items():
                if isinstance(value, (str, int, float, bool)):
                    env[f"INPUT_{key.upper()}"] = str(value)
            
            # Execute with timeout
            result = subprocess.run(
                ["bash", "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Bash execution failed: {result.stderr}")
            
            # Return stdout as result
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Bash execution timed out after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Bash execution error: {str(e)}")