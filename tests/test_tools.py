import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mycli_plus.tools.create_tool import create_tool
from mycli_plus.tools.shell_tool import run_command
from mycli_plus.tools.system_tools import read_file, replace_in_file, write_file


class WorkspaceToolTests(unittest.TestCase):
    def test_file_tools_operate_inside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("pathlib.Path.cwd", return_value=Path(directory)):
            self.assertIn("Wrote", write_file("notes.txt", "hello"))
            self.assertEqual(read_file("notes.txt"), "hello")
            self.assertIn("Updated", replace_in_file("notes.txt", "hello", "world"))
            self.assertEqual(read_file("notes.txt"), "world")

    def test_file_tools_reject_paths_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("pathlib.Path.cwd", return_value=Path(directory)):
            with self.assertRaises(ValueError):
                read_file("../outside.txt")

    def test_leading_workspace_prefix_is_not_nested(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("pathlib.Path.cwd", return_value=Path(directory)):
            write_file("workspace/generated_tools/a.py", "x")
            self.assertTrue((Path(directory) / "workspace" / "generated_tools" / "a.py").is_file())
            self.assertFalse((Path(directory) / "workspace" / "workspace").exists())


class CreateToolTests(unittest.TestCase):
    ARGS = dict(
        tool_name="repeat",
        tool_description="Repeat text.",
        parameters_properties={"text": {"type": "string"}},
        required_parameters=["text"],
    )

    def test_writes_complete_tool_in_one_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("pathlib.Path.cwd", return_value=Path(directory)):
            create_tool(**self.ARGS, implementation="def repeat(text):\n    return text * 2")
            source = (Path(directory) / "workspace" / "generated_tools" / "repeat.py").read_text()
            self.assertIn("SCHEMA", source)
            namespace: dict = {}
            exec(source, namespace)
            self.assertEqual(namespace["repeat"]("a"), "aa")

    def test_rejects_bad_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("pathlib.Path.cwd", return_value=Path(directory)):
            for bad in ("def (", "def other():\n    pass"):
                with self.assertRaises(ValueError):
                    create_tool(**self.ARGS, implementation=bad)
            self.assertFalse((Path(directory) / "workspace").exists())


class RunCommandTests(unittest.TestCase):
    def test_runs_in_workspace_and_reports_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("pathlib.Path.cwd", return_value=Path(directory)):
            result = run_command("pwd; echo hi; exit 3")
            self.assertTrue(result.startswith("exit code 3"))
            self.assertIn("workspace", result)
            self.assertIn("hi", result)

    def test_times_out(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("pathlib.Path.cwd", return_value=Path(directory)):
            self.assertIn("Timed out", run_command("sleep 5", timeout_seconds=1))

    def test_hides_secrets_and_truncates(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch("pathlib.Path.cwd", return_value=Path(directory)), patch.dict(
            "os.environ", {"GROQ_API_KEY": "sekret", "PLAIN": "ok"}
        ):
            self.assertNotIn("sekret", run_command("env"))
            self.assertIn("PLAIN=ok", run_command("env"))
            self.assertIn("truncated", run_command("head -c 20000 /dev/zero | tr '\\0' a"))

    def test_rejects_empty_command(self) -> None:
        with self.assertRaises(ValueError):
            run_command("  ")


if __name__ == "__main__":
    unittest.main()
