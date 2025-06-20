"""
Job node handler - executes code in a sandboxed environment
"""

import json
import subprocess
import tempfile
import os
import logging
import time
from typing import Dict, Any
from ..schemas.job import JobNodeProps, SupportedLanguage
from ..types import ExecutionContext
from src.__generated__.models import NodeOutput
from ..decorators import node

logger = logging.getLogger(__name__)


@node(
    node_type="job",
    schema=JobNodeProps,
    description="Execute code in Python, JavaScript, or Bash"
)
async def job_handler(
    props: JobNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any],
    services: Dict[str, Any]
) -> Any:
    """Handle Job node execution with code sandboxing"""
    
    code = props.code
    language = props.language
    timeout = props.timeout
    
    # Substitute variables in code
    code = _substitute_variables(code, inputs)
    
    logger.info(f"Executing {language} code with timeout {timeout}s")
    start_time = time.time()
    
    try:
        if language == SupportedLanguage.PYTHON:
            result = await _execute_python(code, inputs, timeout)
        elif language == SupportedLanguage.JAVASCRIPT:
            result = await _execute_javascript(code, inputs, timeout)
        elif language == SupportedLanguage.BASH:
            result = await _execute_bash(code, inputs, timeout)
        else:
            raise ValueError(f"Unsupported language: {language}")
        
        logger.info(f"Code execution completed successfully")
        
        # Return unified NodeOutput format
        return NodeOutput(
            value=result,
            metadata={
                "language": language.value if language else None,
                "executionTime": time.time() - start_time,
                "timeout": timeout
            }
        )
        
    except subprocess.TimeoutExpired:
        error_msg = f"{language} execution timed out after {timeout} seconds"
        logger.error(error_msg)
        return NodeOutput(
            value=None,
            metadata={
                "error": error_msg,
                "language": language.value if language else None,
                "executionTime": time.time() - start_time,
                "timedOut": True
            }
        )
    except Exception as e:
        error_msg = f"{language} execution error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return NodeOutput(
            value=None,
            metadata={
                "error": error_msg,
                "language": language.value if language else None,
                "executionTime": time.time() - start_time
            }
        )


def _substitute_variables(code: str, inputs: Dict[str, Any]) -> str:
    """Substitute template variables in code"""
    for key, value in inputs.items():
        # Handle different placeholder formats
        code = code.replace(f"{{{{{key}}}}}", str(value))
        code = code.replace(f"${{{key}}}", str(value))
        code = code.replace(f"${key}", str(value))
    return code


async def _execute_python(code: str, inputs: Dict[str, Any], timeout: int) -> Any:
    """Execute Python code in an isolated subprocess"""
    
    # Create execution script
    script = f"""
import json
import sys

# Define inputs
inputs = {json.dumps(inputs)}

# User code
{code}

# Output result as JSON
if 'result' in locals():
    print(json.dumps(result))
else:
    # If no explicit result, try to capture the last expression
    print(json.dumps(None))
"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        f.flush()
        temp_file = f.name
    
    try:
        # Execute in subprocess
        result = subprocess.run(
            ["python", temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Python execution failed:\n{result.stderr}")
        
        # Parse output
        output = result.stdout.strip()
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # If not valid JSON, return as string
                return output
        return None
        
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass


async def _execute_javascript(code: str, inputs: Dict[str, Any], timeout: int) -> Any:
    """Execute JavaScript code using Node.js"""
    
    # Create execution script
    script = f"""
const inputs = {json.dumps(inputs)};

// User code
{code}

// Output result as JSON
if (typeof result !== 'undefined') {{
    console.log(JSON.stringify(result));
}} else {{
    console.log(JSON.stringify(null));
}}
"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(script)
        f.flush()
        temp_file = f.name
    
    try:
        # Execute in subprocess
        result = subprocess.run(
            ["node", temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"JavaScript execution failed:\n{result.stderr}")
        
        # Parse output
        output = result.stdout.strip()
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # If not valid JSON, return as string
                return output
        return None
        
    except FileNotFoundError:
        raise RuntimeError("Node.js not found. Please install Node.js to execute JavaScript code.")
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass


async def _execute_bash(code: str, inputs: Dict[str, Any], timeout: int) -> Any:
    """Execute Bash code with input variables as environment variables"""
    
    # Prepare environment with input variables
    env = os.environ.copy()
    for key, value in inputs.items():
        if isinstance(value, (str, int, float, bool)):
            # Make variables available as INPUT_VARNAME
            env[f"INPUT_{key.upper()}"] = str(value)
            # Also make them available as just VARNAME for convenience
            env[key.upper()] = str(value)
    
    try:
        # Execute bash command
        result = subprocess.run(
            ["bash", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Bash execution failed:\n{result.stderr}")
        
        # Return stdout as result
        output = result.stdout.strip()
        
        # Try to parse as JSON if it looks like JSON
        if output and (output.startswith('{') or output.startswith('[')):
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass
        
        return output if output else None
        
    except FileNotFoundError:
        raise RuntimeError("Bash not found. This system may not support bash execution.")