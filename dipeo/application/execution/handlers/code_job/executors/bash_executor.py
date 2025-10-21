"""Bash/Shell language executor."""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import aiofiles

from .base import BaseCodeExecutor


class BashExecutor(BaseCodeExecutor):
    async def execute_file(
        self, file_path: Path, inputs: dict[str, Any], timeout: int, function_name: str = "main"
    ) -> Any:
        env = dict(os.environ)
        if inputs:
            env["INPUT_KEYS"] = " ".join(inputs.keys())

            for key, value in inputs.items():
                if isinstance(value, dict | list):
                    env[f"INPUT_{key}"] = json.dumps(value)
                else:
                    env[f"INPUT_{key}"] = str(value)

        if sys.platform == "win32":
            bash_cmd = None
            possible_bash_paths = [
                "bash.exe",
                "sh.exe",
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\Program Files (x86)\Git\bin\bash.exe",
                r"C:\Windows\System32\bash.exe",
            ]

            for bash_path in possible_bash_paths:
                try:
                    test_proc = await asyncio.create_subprocess_exec(
                        bash_path,
                        "-c",
                        "echo test",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, _ = await test_proc.communicate()
                    if test_proc.returncode == 0 and stdout.strip() == b"test":
                        bash_cmd = bash_path
                        break
                except Exception:
                    continue

            if not bash_cmd:
                raise Exception(
                    "Bash interpreter not found. Please install Git for Windows or WSL."
                )

            async with aiofiles.open(file_path) as f:
                script_content = await f.read()

            proc = await asyncio.create_subprocess_exec(
                bash_cmd,
                "-s",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(file_path.parent),
            )
        else:
            if not os.access(file_path, os.X_OK):
                os.chmod(file_path, os.stat(file_path).st_mode | 0o111)

            proc = await asyncio.create_subprocess_exec(
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(file_path.parent),
            )

        script_content = locals().get("script_content")
        try:
            if sys.platform == "win32" and script_content is not None:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=script_content.encode()), timeout=timeout
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
        self, code: str, inputs: dict[str, Any], timeout: int, function_name: str = "main"
    ) -> Any:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False, encoding="utf-8"
        ) as temp_file:
            if not code.startswith("#!"):
                temp_file.write("#!/bin/bash\n")
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            if sys.platform != "win32":
                os.chmod(temp_file_path, os.stat(temp_file_path).st_mode | 0o111)

            result = await self.execute_file(Path(temp_file_path), inputs, timeout)
            return result
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
