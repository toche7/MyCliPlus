from typing import Any

import httpx

from mycli_plus.config import Settings


def chat(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    *,
    settings: Settings,
) -> dict[str, Any]:
    """Send a chat-completions request and return the assistant message."""
    body: dict[str, Any] = {
        "model": settings.model,
        "messages": messages,
        "max_tokens": settings.max_tokens,
    }
    if tools:
        body["tools"] = tools

    response = httpx.post(
        settings.api_url,
        headers={"Authorization": f"Bearer {settings.api_key}"},
        json=body,
        timeout=settings.timeout_seconds,
    )
    response.raise_for_status()

    payload = response.json()
    return payload["choices"][0]["message"]
