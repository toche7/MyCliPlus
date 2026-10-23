from collections.abc import Callable
from typing import Any

from mycli_plus.agent import run_agent
from mycli_plus.config import Settings
from mycli_plus.registry import ToolRegistry


class ChatSession:
    def __init__(
        self,
        settings: Settings,
        registry: ToolRegistry | None = None,
        max_history: int = 20,
    ) -> None:
        if max_history < 1:
            raise ValueError("max_history must be at least 1.")
        self.settings = settings
        self.registry = registry or ToolRegistry()
        self.max_history = max_history
        prompt = (
            "You are a helpful AI assistant operating in a terminal. "
            "Use tools only for the user's requested task. "
            "Never claim an action succeeded unless the tool result confirms it."
        )
        if self.registry.mode == "self_improve":
            prompt += (
                " File tools are restricted to ./workspace (paths are relative to "
                "it). To add a new tool, call create_tool exactly once with the "
                "complete Python source in `implementation`; never create tool "
                "files with the file tools. Use run_command (bash, cwd ./workspace) "
                "to test or build, for example python -m py_compile on a new tool. "
                "Then ask the user to run /reload."
            )
        self.system_prompt = {"role": "system", "content": prompt}
        self.messages: list[dict[str, Any]] = [self.system_prompt]
        self.on_event: Callable[..., None] | None = None

    def send_message(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        response = run_agent(
            self.messages,
            settings=self.settings,
            registry=self.registry,
            on_event=self.on_event,
        )
        self._trim_history(response)
        return response

    def _trim_history(self, final_response: str) -> None:
        if len(self.messages) <= self.max_history + 1:
            return

        retained_turn = next(
            (
                index
                for index, message in enumerate(self.messages[1:], start=1)
                if message.get("role") == "user"
                and len(self.messages) - index <= self.max_history
            ),
            None,
        )
        if retained_turn is not None:
            self.messages = [self.system_prompt, *self.messages[retained_turn:]]
            return

        latest_user = max(
            index
            for index, message in enumerate(self.messages)
            if message.get("role") == "user"
        )
        latest_turn = [
            self.messages[latest_user],
            {"role": "assistant", "content": final_response},
        ]
        self.messages = [self.system_prompt, *latest_turn[-self.max_history :]]
