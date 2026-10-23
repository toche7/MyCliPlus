import os
from dataclasses import dataclass

from mycli_plus.registry import MODE_LIMITED, MODES


DEFAULT_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3.8-27b"


@dataclass(frozen=True)
class Settings:
    api_key: str
    api_url: str = DEFAULT_API_URL
    model: str = DEFAULT_MODEL
    max_tokens: int = 800
    timeout_seconds: float = 60.0
    enabled_tools: tuple[str, ...] | None = None
    mode: str = MODE_LIMITED
    verbose: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")

        configured_tools = os.environ.get("MYCLI_TOOLS", "").strip()
        enabled_tools = (
            tuple(
                dict.fromkeys(
                    name.strip()
                    for name in configured_tools.split(",")
                    if name.strip()
                )
            )
            if configured_tools
            else None
        )

        mode = os.environ.get("MYCLI_MODE", "").strip().lower() or MODE_LIMITED
        if mode not in MODES:
            raise ValueError(
                f"MYCLI_MODE must be one of: {', '.join(MODES)} (got '{mode}')."
            )

        return cls(
            api_key=api_key,
            api_url=os.environ.get("GROQ_API_URL", DEFAULT_API_URL).strip(),
            model=os.environ.get("GROQ_MODEL", DEFAULT_MODEL).strip(),
            enabled_tools=enabled_tools,
            mode=mode,
            verbose=os.environ.get("MYCLI_VERBOSE", "").strip().lower()
            in {"1", "true", "yes", "on"},
        )
