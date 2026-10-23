import os
import subprocess
from pathlib import Path

SELF_IMPROVE_ONLY = True

DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 300
MAX_OUTPUT_CHARS = 8000
_SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")

SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_command",
        "description": (
            "Run a bash command in ./workspace (for example to test or build a "
            "tool: python -m py_compile, pip install, ls). Returns the exit "
            "code and combined output. Commands time out."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout_seconds": {
                    "type": "integer",
                    "description": f"Default {DEFAULT_TIMEOUT}, max {MAX_TIMEOUT}.",
                },
            },
            "required": ["command"],
        },
    },
}


def _clean_env() -> dict[str, str]:
    """Hide secrets such as GROQ_API_KEY from model-run commands."""
    return {
        name: value
        for name, value in os.environ.items()
        if not any(marker in name.upper() for marker in _SECRET_MARKERS)
    }


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n... (+{len(text) - MAX_OUTPUT_CHARS} chars truncated)"


def run_command(command: str, timeout_seconds: int = DEFAULT_TIMEOUT) -> str:
    """Run a bash command with cwd=./workspace, a timeout and capped output."""
    if not isinstance(command, str) or not command.strip():
        raise ValueError("command must be a non-empty string.")
    timeout = max(1, min(int(timeout_seconds), MAX_TIMEOUT))

    workspace = Path.cwd() / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(
            ["bash", "-c", command],
            cwd=workspace,
            env=_clean_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        partial = error.stdout if isinstance(error.stdout, str) else ""
        return f"Timed out after {timeout}s.\n{_truncate(partial)}".rstrip()
    except FileNotFoundError as error:
        raise ValueError("bash is not available on this system.") from error

    output = _truncate((completed.stdout or "") + (completed.stderr or ""))
    return f"exit code {completed.returncode}\n{output}".rstrip()
