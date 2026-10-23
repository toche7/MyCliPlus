from pathlib import Path
from typing import Callable

SELF_IMPROVE_ONLY = True


def _workspace_path(path: str) -> Path:
    root = (Path.cwd() / "workspace").resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        # Models often write "workspace/x" although paths are already relative to it.
        if candidate.parts[:1] == ("workspace",):
            candidate = Path(*candidate.parts[1:])
        candidate = root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("File tools can only access paths inside ./workspace.") from error
    return resolved


def read_file(path: str) -> str:
    target = _workspace_path(path)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {target}")
    return target.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    target = _workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    relative_path = target.relative_to((Path.cwd() / "workspace").resolve())
    return f"Wrote {len(content)} characters to {relative_path}."


def replace_in_file(path: str, old_text: str, new_text: str) -> str:
    target = _workspace_path(path)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {target}")
    content = target.read_text(encoding="utf-8")
    if old_text not in content:
        raise ValueError("The requested text was not found.")
    target.write_text(content.replace(old_text, new_text), encoding="utf-8")
    relative_path = target.relative_to((Path.cwd() / "workspace").resolve())
    return f"Updated {relative_path}."


SYSTEM_TOOLS: dict[str, tuple[dict, Callable[..., str]]] = {
    "read_file": (
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a text file inside ./workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
        read_file,
    ),
    "write_file": (
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write a text file inside ./workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        write_file,
    ),
    "replace_in_file": (
        {
            "type": "function",
            "function": {
                "name": "replace_in_file",
                "description": "Replace exact text inside a file in ./workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"},
                    },
                    "required": ["path", "old_text", "new_text"],
                },
            },
        },
        replace_in_file,
    ),
}
