import ast
import json
import re
from pathlib import Path
from typing import Any

SELF_IMPROVE_ONLY = True

SCHEMA = {
    "type": "function",
    "function": {
        "name": "create_tool",
        "description": (
            "Create a complete tool in one call. Provide the full Python source "
            "of the function in `implementation` (a `def <tool_name>(...)` "
            "returning a string). It is saved to the correct place; do not use "
            "file tools for it. The user then runs /reload to load it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string"},
                "tool_description": {"type": "string"},
                "parameters_properties": {"type": "object"},
                "required_parameters": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "implementation": {
                    "type": "string",
                    "description": "Python source defining def <tool_name>(...).",
                },
            },
            "required": [
                "tool_name",
                "tool_description",
                "parameters_properties",
                "required_parameters",
                "implementation",
            ],
        },
    },
}


def create_tool(
    tool_name: str,
    tool_description: str,
    parameters_properties: dict[str, Any],
    required_parameters: list[str],
    implementation: str,
) -> str:
    """Write a tool module under ./workspace/generated_tools."""
    name = tool_name.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,49}", name):
        raise ValueError("Tool name must be a simple Python identifier.")
    if not isinstance(parameters_properties, dict):
        raise ValueError("parameters_properties must be an object.")
    if not all(isinstance(key, str) for key in parameters_properties):
        raise ValueError("Parameter names must be strings.")
    if not isinstance(required_parameters, list) or not all(
        isinstance(item, str) for item in required_parameters
    ):
        raise ValueError("required_parameters must be a list of strings.")
    if not set(required_parameters).issubset(parameters_properties):
        raise ValueError("Every required parameter must be defined in the properties.")

    if not isinstance(implementation, str):
        raise ValueError("implementation must be a string of Python source.")
    try:
        tree = ast.parse(implementation)
    except SyntaxError as error:
        raise ValueError(f"implementation has a syntax error: {error}") from error
    if not any(
        isinstance(node, ast.FunctionDef) and node.name == name for node in tree.body
    ):
        raise ValueError(f"implementation must define a top-level function '{name}'.")

    schema = {
        "type": "function",
        "function": {
            "name": name,
            "description": tool_description,
            "parameters": {
                "type": "object",
                "properties": parameters_properties,
                "required": required_parameters,
            },
        },
    }
    destination = (Path.cwd() / "workspace" / "generated_tools").resolve()
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"{name}.py"
    target.write_text(
        "SCHEMA = "
        + json.dumps(schema, ensure_ascii=False, indent=4)
        + "\n\n\n"
        + implementation.strip()
        + "\n",
        encoding="utf-8",
    )
    return (
        f"Created tool {target.relative_to(Path.cwd().resolve())}. Ask the user to run "
        "/reload to load it."
    )
