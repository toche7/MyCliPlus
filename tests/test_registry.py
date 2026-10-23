import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mycli_plus.config import Settings
from mycli_plus.registry import ToolRegistry


class ToolSelectionTests(unittest.TestCase):
    def test_settings_parse_selected_tools(self) -> None:
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "test", "MYCLI_TOOLS": " run_command, read_file,run_command "},
            clear=True,
        ):
            settings = Settings.from_env()

        self.assertEqual(settings.enabled_tools, ("run_command", "read_file"))

    def test_settings_default_to_all_tools(self) -> None:
        with patch.dict(os.environ, {"GROQ_API_KEY": "test"}, clear=True):
            settings = Settings.from_env()

        self.assertIsNone(settings.enabled_tools)

    def test_registry_only_exposes_selected_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "pathlib.Path.cwd", return_value=Path(directory)
        ):
            registry = ToolRegistry(
                enabled_tools=("run_command", "read_file"), mode="self_improve"
            )

        self.assertEqual(set(registry.functions), {"run_command", "read_file"})
        self.assertEqual(
            {schema["function"]["name"] for schema in registry.schemas},
            {"run_command", "read_file"},
        )
        self.assertIn("Unknown tool", registry.dispatch("write_file", "{}"))

    def test_registry_rejects_unknown_tool_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "MYCLI_TOOLS: missing"):
            ToolRegistry(enabled_tools=("missing",))

    def test_verbose_setting(self) -> None:
        with patch.dict(os.environ, {"GROQ_API_KEY": "t", "MYCLI_VERBOSE": "true"}, clear=True):
            self.assertTrue(Settings.from_env().verbose)
        with patch.dict(os.environ, {"GROQ_API_KEY": "t"}, clear=True):
            self.assertFalse(Settings.from_env().verbose)

    def test_mode_defaults_to_limited_and_validates(self) -> None:
        with patch.dict(os.environ, {"GROQ_API_KEY": "test"}, clear=True):
            self.assertEqual(Settings.from_env().mode, "limited")
        with patch.dict(
            os.environ, {"GROQ_API_KEY": "test", "MYCLI_MODE": "bogus"}, clear=True
        ):
            with self.assertRaises(ValueError):
                Settings.from_env()


class ModeTests(unittest.TestCase):
    def test_limited_mode_has_no_privileged_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "pathlib.Path.cwd", return_value=Path(directory)
        ):
            self.assertEqual(set(ToolRegistry(mode="limited").functions), set())

    def test_self_improve_mode_has_all_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "pathlib.Path.cwd", return_value=Path(directory)
        ):
            tools = set(ToolRegistry(mode="self_improve").functions)
        self.assertEqual(
            tools,
            {"create_tool", "read_file", "write_file", "replace_in_file", "run_command"},
        )

    def test_reload_loads_generated_tools_only_in_self_improve_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "pathlib.Path.cwd", return_value=Path(directory)
        ):
            generated = Path(directory) / "workspace" / "generated_tools"
            generated.mkdir(parents=True)
            improving = ToolRegistry(mode="self_improve")
            limited = ToolRegistry(mode="limited")
            self.assertNotIn("shout", improving.functions)

            (generated / "shout.py").write_text(
                'SCHEMA = {"type": "function", "function": {"name": "shout", '
                '"description": "x", "parameters": {"type": "object", '
                '"properties": {"text": {"type": "string"}}, "required": ["text"]}}}\n'
                "def shout(text):\n    return text.upper()\n",
                encoding="utf-8",
            )
            (generated / "broken.py").write_text("def (", encoding="utf-8")

            message = improving.reload()
            self.assertIn("shout", improving.functions)
            self.assertIn("Skipped generated tool broken.py", message)
            self.assertEqual(improving.dispatch("shout", '{"text": "hi"}'), "HI")

            limited.reload()
            self.assertNotIn("shout", limited.functions)

    def test_failed_reload_keeps_previous_tools(self) -> None:
        registry = ToolRegistry(enabled_tools=("read_file",), mode="self_improve")
        registry.enabled_tools = ("missing",)
        self.assertIn("Reload failed", registry.reload())
        self.assertIn("read_file", registry.functions)

    def test_tool_whitelist_does_not_hide_generated_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "pathlib.Path.cwd", return_value=Path(directory)
        ):
            generated = Path(directory) / "workspace" / "generated_tools"
            generated.mkdir(parents=True)
            registry = ToolRegistry(enabled_tools=("read_file",), mode="self_improve")
            (generated / "echo.py").write_text(
                'SCHEMA = {"type": "function", "function": {"name": "echo", '
                '"description": "x", "parameters": {"type": "object", '
                '"properties": {}, "required": []}}}\n'
                "def echo():\n    return 'ok'\n",
                encoding="utf-8",
            )
            (generated / "noschema.py").write_text(
                "def noschema():\n    return 1\n", encoding="utf-8"
            )
            message = registry.reload()
            self.assertEqual(set(registry.functions), {"read_file", "echo"})
            self.assertIn("noschema.py", message)


if __name__ == "__main__":
    unittest.main()
