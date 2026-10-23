import json
from pathlib import Path
from typing import Any, Callable

from mycli_plus.dynamic_loader import load_dynamic_tools

MODE_LIMITED = "limited"
MODE_SELF_IMPROVE = "self_improve"
MODES = (MODE_LIMITED, MODE_SELF_IMPROVE)


class ToolRegistry:
    def __init__(
        self,
        enabled_tools: tuple[str, ...] | None = None,
        mode: str = MODE_LIMITED,
    ) -> None:
        if mode not in MODES:
            raise ValueError(f"Unknown mode '{mode}'. Use one of: {', '.join(MODES)}.")
        self.enabled_tools = enabled_tools
        self.mode = mode
        self.schemas: list[dict[str, Any]] = []
        self.functions: dict[str, Callable[..., Any]] = {}
        self._load()

    def _load(self) -> str:
        self_improve = self.mode == MODE_SELF_IMPROVE
        warnings: list[str] = []
        schemas, functions = load_dynamic_tools(
            self_improve=self_improve,
            generated_dir=(
                Path.cwd() / "workspace" / "generated_tools" if self_improve else None
            ),
            warnings=warnings,
            enabled_tools=self.enabled_tools,
        )

        self.schemas, self.functions = schemas, functions
        message = f"Reloaded tools: {', '.join(self.functions) or '(none)'}"
        return "\n".join([message, *warnings])

    def reload(self) -> str:
        try:
            return self._load()
        except (ImportError, ValueError) as error:
            return f"Reload failed, keeping previous tools: {error}"

    def dispatch(self, name: str, arguments_json: str) -> str:
        function = self.functions.get(name)
        if function is None:
            return f"Error: Unknown tool '{name}'."
        try:
            arguments = json.loads(arguments_json) if arguments_json else {}
            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must be a JSON object.")
            return str(function(**arguments))
        except Exception as error:
            return f"Error executing {name}: {type(error).__name__}: {error}"
