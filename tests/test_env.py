import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mycli_plus.env import load_env_file


class EnvLoaderTests(unittest.TestCase):
    def _write(self, directory: str, text: str) -> Path:
        path = Path(directory) / ".env"
        path.write_text(text, encoding="utf-8")
        return path

    def test_loads_values_and_skips_comments_blanks_and_empty_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = self._write(
                directory,
                "# comment\n\nA=1\nexport B=\"two words\"\nC='x'\nD=val # note\nE=\n",
            )
            self.assertTrue(load_env_file(path))
            self.assertEqual(os.environ["A"], "1")
            self.assertEqual(os.environ["B"], "two words")
            self.assertEqual(os.environ["C"], "x")
            self.assertEqual(os.environ["D"], "val")
            self.assertNotIn("E", os.environ)

    def test_existing_environment_wins(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"A": "shell"}, clear=True):
            load_env_file(self._write(directory, "A=file\n"))
            self.assertEqual(os.environ["A"], "shell")

    def test_missing_file_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(load_env_file(Path(directory) / ".env"))


if __name__ == "__main__":
    unittest.main()
