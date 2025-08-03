"""Bash/Shell language executor."""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseCodeExecutor


class BashExecutor(BaseCodeExecutor):
    """Executor for Bash/Shell scripts."""
    
    async def execute_file(
        self,
        file_path: Path,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"  # Ignored for bash
    ) -> Any:
        """Execute Bash script file with inputs as environment variables."""
        # Set up environment variables from inputs
        env = dict(os.environ)
        if inputs:
            # Add a helper variable listing all input keys
            env["INPUT_KEYS"] = " ".join(inputs.keys())
            
            for key, value in inputs.items():
                # Convert values to strings for environment variables
                if isinstance(value, dict | list):
                    env[f"INPUT_{key}"] = json.dumps(value)
                else:
                    env[f"INPUT_{key}"] = str(value)
        
        # On Windows, we need to use bash.exe or sh.exe to run shell scripts
        if sys.platform == "win32":
            # Try to find bash.exe (from Git for Windows, WSL, or other sources)
            bash_cmd = None
            possible_bash_paths = [
                "bash.exe",  # In PATH
                "sh.exe",    # Alternative
                r"C:\Program Files\Git\bin\bash.exe",  # Git for Windows
                r"C:\Program Files (x86)\Git\bin\bash.exe",
                r"C:\Windows\System32\bash.exe",  # WSL
            ]
            
            for bash_path in possible_bash_paths:
                try:
                    # Check if bash exists by running a simple command
                    test_proc = await asyncio.create_subprocess_exec(
                        bash_path, "-c", "echo test",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await test_proc.communicate()
                    if test_proc.returncode == 0 and stdout.strip() == b"test":
                        bash_cmd = bash_path
                        break
                except Exception:
                    continue
            
            if not bash_cmd:
                raise Exception("Bash interpreter not found. Please install Git for Windows or WSL.")
            
            # Read the script content and pass it via stdin to avoid path issues
            with open(file_path) as f:
                script_content = f.read()
            
            # Run the script through bash by passing content via stdin
            proc = await asyncio.create_subprocess_exec(
                bash_cmd, "-s",  # -s flag reads from stdin
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(file_path.parent)
            )
        else:
            # On Unix-like systems, make the script executable and run directly
            if not os.access(file_path, os.X_OK):
                os.chmod(file_path, os.stat(file_path).st_mode | 0o111)
            
            proc = await asyncio.create_subprocess_exec(
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(file_path.parent)
            )
        
        try:
            if sys.platform == "win32" and 'script_content' in locals():
                # Send script content via stdin on Windows
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=script_content.encode()),
                    timeout=timeout
                )
            else:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise TimeoutError(f"Bash execution timed out after {timeout} seconds") from None
        
        if proc.returncode != 0:
            raise Exception(f"Bash execution failed: {stderr.decode()}")
        
        return stdout.decode().strip()
    
    async def execute_inline(
        self,
        code: str,
        inputs: dict[str, Any],
        timeout: int,
        function_name: str = "main"  # Ignored for bash
    ) -> Any:
        """Execute inline Bash code."""
        # Create a temporary file with the bash code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
            # Add shebang if not present
            if not code.startswith('#!'):
                temp_file.write('#!/bin/bash\n')
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # On Unix-like systems, make it executable
            if sys.platform != "win32":
                os.chmod(temp_file_path, os.stat(temp_file_path).st_mode | 0o111)
            
            # Execute using the file-based method
            result = await self.execute_file(Path(temp_file_path), inputs, timeout)
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)