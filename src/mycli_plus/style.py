import os
import sys
from typing import TextIO

RESET = "\033[0m"
USER = "\033[1;36m"  # bold cyan
AGENT = "\033[1;32m"  # bold green
ERROR = "\033[1;31m"  # bold red
DIM = "\033[2m"


def use_color(stream: TextIO) -> bool:
    """Color only real terminals, and respect NO_COLOR / MYCLI_COLOR=0."""
    if os.environ.get("NO_COLOR") or os.environ.get("MYCLI_COLOR", "").strip() == "0":
        return False
    return stream.isatty()


def paint(text: str, color: str, stream: TextIO) -> str:
    return f"{color}{text}{RESET}" if use_color(stream) else text


def prompt(label: str, color: str) -> str:
    """Colored input() prompt; \\001/\\002 keep readline's cursor math correct."""
    if not (use_color(sys.stdout) and sys.stdin.isatty()):
        return label
    return f"\001{color}\002{label}\001{RESET}\002"
