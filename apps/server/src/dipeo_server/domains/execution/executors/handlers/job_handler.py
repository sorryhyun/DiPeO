from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
import textwrap
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Mapping

from ..schemas.job import JobNodeProps
from dipeo_domain import SupportedLanguage
from ..types import RuntimeExecutionContext
from ..decorators import node
from ..base import BaseNodeHandler, log_action
from ..executor_utils import substitute_variables

# Generic helpers (unchanged)

@contextmanager
def _tmp_file(suffix: str, content: str):
    """Write *content* to a temp file that is deleted afterwards."""
    path = Path(tempfile.mkstemp(suffix=suffix)[1])
    try:
        path.write_text(content)
        yield path
    finally:
        try:
            path.unlink()
        except FileNotFoundError:  # already removed
            pass


async def _run(cmd: list[str], timeout: int, env: Dict[str, str] | None = None) -> str:
    """Async wrapper around *subprocess.run* executed in a thread."""
    def _sync():
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    result = await asyncio.to_thread(_sync)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Unknown execution error")
    return result.stdout.strip()


def _try_json(value: str) -> Any:
    """Return parsed JSON if *value* looks like JSON, else *value* itself."""
    if value and value[0] in "[{\"":
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value or None


# Language‑specific executors (unchanged)

async def _exec_python(code: str, inputs: Dict[str, Any], timeout: int) -> Any:
    script = textwrap.dedent(f"""
        import json
        inputs = {json.dumps(inputs, ensure_ascii=False)}
        {code}
        print(json.dumps(locals().get('result')))
    """)
    async with asyncio.Lock():  # avoid race on Windows with py caching
        with _tmp_file('.py', script) as path:
            output = await _run(['python', str(path)], timeout)
    return _try_json(output)


async def _exec_javascript(code: str, inputs: Dict[str, Any], timeout: int) -> Any:
    script = textwrap.dedent(f"""
        const inputs = {json.dumps(inputs, ensure_ascii=False)};
        {code}
        console.log(JSON.stringify(typeof result === 'undefined' ? null : result));
    """)
    with _tmp_file('.js', script) as path:
        output = await _run(['node', str(path)], timeout)
    return _try_json(output)


async def _exec_bash(code: str, inputs: Dict[str, Any], timeout: int) -> Any:
    env = {f"INPUT_{k.upper()}": str(v) for k, v in inputs.items() if isinstance(v, (str, int, float, bool))}
    env.update({k.upper(): str(v) for k, v in inputs.items() if isinstance(v, (str, int, float, bool))})
    output = await _run(['bash', '-c', code], timeout, env=env)
    return _try_json(output)


_EXECUTORS: Mapping[SupportedLanguage, Callable[[str, Dict[str, Any], int], Any]] = {
    SupportedLanguage.python: _exec_python,
    SupportedLanguage.javascript: _exec_javascript,
    SupportedLanguage.bash: _exec_bash,
}


# --------------------------------------------------------------------------- #
# Refactored handler using BaseNodeHandler
# --------------------------------------------------------------------------- #

@node(
    node_type="job",
    schema=JobNodeProps,
    description="Execute code snippets in Python, JavaScript, or Bash"
)
class JobHandler(BaseNodeHandler):
    """Unified job executor node using BaseNodeHandler.
    
    This refactored version eliminates ~40 lines of boilerplate code
    by inheriting common functionality from BaseNodeHandler.
    """
    
    async def _execute_core(
        self,
        props: JobNodeProps,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]  # noqa: ARG002
    ) -> Any:
        """Execute the job with the specified language and code.
        
        All error handling, timing, and metadata building is handled
        by the base class.
        """
        language = props.language
        executor = _EXECUTORS.get(language)
        if executor is None:
            raise ValueError(f"Unsupported language: {language}")
        
        code = substitute_variables(props.code, inputs)
        timeout = props.timeout
        
        # Log what we're about to do
        log_action(
            self.logger,
            context.current_node_id,
            f"Executing {language.value} job",
            language=language.value,
            timeout=timeout
        )
        
        # Execute and return result
        # The base class handles timing and exceptions
        return await executor(code, inputs, timeout)
    
    def _build_metadata(
        self,
        start_time: float,
        props: JobNodeProps,
        context: RuntimeExecutionContext,
        result: Any
    ) -> Dict[str, Any]:
        """Add job-specific metadata to the base metadata."""
        metadata = super()._build_metadata(start_time, props, context, result)
        metadata.update({
            "language": props.language.value,
            "timeout": props.timeout,
            "timedOut": False,
        })
        return metadata