import time
from collections.abc import Callable
from typing import Any

from mycli_plus.client import chat
from mycli_plus.config import Settings
from mycli_plus.registry import ToolRegistry


def run_agent(
    messages: list[dict[str, Any]],
    *,
    settings: Settings,
    registry: ToolRegistry,
    max_steps: int = 20,
    on_event: Callable[..., None] | None = None,
    chat_fn: Callable[..., dict[str, Any]] = chat,
) -> str:
    """Run model and tool-call rounds until the model returns a final answer."""
    latest_user = (
        messages[-1]["content"].strip()
        if messages and messages[-1].get("role") == "user"
        else ""
    )
    if latest_user == "/reload":
        result = registry.reload()
        messages.append({"role": "assistant", "content": result})
        return result

    def emit(kind: str, **data: Any) -> None:
        if on_event:
            on_event(kind, **data)

    for step in range(1, max_steps + 1):
        emit("model_call", step=step, messages=len(messages), tools=len(registry.schemas))
        started = time.perf_counter()
        reply = chat_fn(messages, registry.schemas or None, settings=settings)
        calls = reply.get("tool_calls") or []
        emit(
            "model_reply",
            step=step,
            seconds=time.perf_counter() - started,
            content=reply.get("content") or "",
            tool_calls=len(calls),
        )
        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": reply.get("content") or "",
        }
        if calls:
            assistant_message["tool_calls"] = calls
        messages.append(assistant_message)

        if not calls:
            return assistant_message["content"]

        for call in calls:
            function = call["function"]
            name = function["name"]
            arguments = function.get("arguments", "{}")
            emit("tool_call", name=name, arguments=arguments)
            started = time.perf_counter()
            result = registry.dispatch(name, arguments)
            emit(
                "tool_result",
                name=name,
                result=result,
                seconds=time.perf_counter() - started,
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                }
            )

    return f"[stopped after {max_steps} steps without a final answer]"
