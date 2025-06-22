"""Simplified validation helpers using Pydantic."""

from typing import Optional


class CodeValidator:
    """Validator for code safety."""

    DANGEROUS_PATTERNS = {
        "python": {
            "import os",
            "import subprocess",
            "__import__",
            "compile(",
            "exec(",
            "eval(",
        },
        "javascript": {
            "require('fs')",
            "require('child_process')",
            "eval(",
            "Function(",
        },
        "bash": {"rm -rf", "sudo", "> /dev/", "dd if=", "mkfs", ":(){ :|:& };:"},
    }

    @classmethod
    def validate(cls, code: str, language: str, strict: bool = True) -> Optional[str]:
        """Validate code for dangerous patterns."""
        patterns = cls.DANGEROUS_PATTERNS.get(language, set())

        for pattern in patterns:
            if pattern in code:
                if strict:
                    return f"Code contains dangerous operation: {pattern}"

        return None
