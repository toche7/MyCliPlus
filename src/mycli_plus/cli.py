import sys
from typing import Any

import httpx

from mycli_plus.config import Settings
from mycli_plus.env import load_env_file
from mycli_plus.registry import ToolRegistry
from mycli_plus.session import ChatSession
from mycli_plus.style import AGENT, DIM, ERROR, USER, paint, prompt


def _clip(text: str, limit: int = 300) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else f"{text[:limit]}... (+{len(text) - limit} chars)"


def _agent(text: str, color: str = AGENT) -> str:
    return f"{paint('Agent:', color, sys.stdout)} {text}"


def print_event(kind: str, **data: Any) -> None:
    """Print live agent activity to stderr so normal output stays clean."""
    if kind == "model_call":
        line = (
            f"[step {data['step']}] asking model "
            f"({data['messages']} messages, {data['tools']} tools)"
        )
    elif kind == "model_reply":
        action = (
            f"requested {data['tool_calls']} tool call(s)"
            if data["tool_calls"]
            else "final answer"
        )
        line = f"[step {data['step']}] model replied in {data['seconds']:.1f}s: {action}"
        if data["content"] and data["tool_calls"]:
            line += f"\n    thought: {_clip(data['content'])}"
    elif kind == "tool_call":
        line = f"  -> {data['name']}({_clip(data['arguments'])})"
    elif kind == "tool_result":
        line = f"  <- {data['name']} ({data['seconds']:.2f}s): {_clip(data['result'])}"
    else:
        return
    print(paint(line, DIM, sys.stderr), file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    load_env_file()
    args = sys.argv[1:] if argv is None else argv
    try:
        settings = Settings.from_env()
    except ValueError as error:
        print(paint(f"Configuration error: {error}", ERROR, sys.stderr), file=sys.stderr)
        return 2

    try:
        registry = ToolRegistry(enabled_tools=settings.enabled_tools, mode=settings.mode)
    except ValueError as error:
        print(paint(f"Configuration error: {error}", ERROR, sys.stderr), file=sys.stderr)
        return 2
    session = ChatSession(settings, registry=registry)
    verbose = settings.verbose or "--verbose" in args or "-v" in args
    session.on_event = print_event if verbose else None
    print(
        f"MyCliPlus ({settings.mode} mode, verbose {'on' if verbose else 'off'}) "
        "is ready. Use /tools, /verbose or /quit."
    )

    while True:
        try:
            user_message = input(prompt("You: ", USER)).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0
        if not user_message:
            continue
        if user_message in {"/quit", "/exit"}:
            print("Goodbye.")
            return 0
        if user_message == "/verbose":
            verbose = not verbose
            session.on_event = print_event if verbose else None
            print(f"Verbose {'on' if verbose else 'off'}.")
            continue
        if user_message == "/tools":
            print("Available tools: " + ", ".join(registry.functions))
            continue

        try:
            response = session.send_message(user_message)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 429:
                print(_agent("Rate limit reached (HTTP 429). Please wait and try again.", ERROR))
            else:
                print(
                    _agent(
                        f"API request failed with HTTP {error.response.status_code}: "
                        f"{error.response.text}",
                        ERROR,
                    )
                )
        except httpx.RequestError as error:
            print(_agent(f"Could not reach the API: {error}", ERROR))
        else:
            print(_agent(response))


if __name__ == "__main__":
    raise SystemExit(main())
