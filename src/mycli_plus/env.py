import os
from pathlib import Path


def _parse_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export "):].lstrip()
    key, separator, value = line.partition("=")
    key = key.strip()
    if not separator or not key:
        return None

    value = value.strip()
    if value[:1] in {'"', "'"}:
        end = value.find(value[0], 1)
        value = value[1:end] if end != -1 else value[1:]
    else:
        value = value.split(" #", 1)[0].strip()
    return key, value


def load_env_file(path: Path | None = None) -> bool:
    """Load KEY=VALUE pairs from a .env file without overriding existing variables.

    Returns True if the file existed. Empty values are ignored so that a blank
    template entry (for example ``GROQ_API_KEY=``) does not mask a real setting.
    """
    env_path = path or Path.cwd() / ".env"
    if not env_path.is_file():
        return False

    for line in env_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_line(line)
        if parsed is None:
            continue
        key, value = parsed
        if value and not os.environ.get(key):
            os.environ[key] = value
    return True
