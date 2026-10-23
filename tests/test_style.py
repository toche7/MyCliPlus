import io
import os
import unittest
from unittest.mock import patch

from mycli_plus import style


class FakeTty(io.StringIO):
    def isatty(self) -> bool:
        return True


class StyleTests(unittest.TestCase):
    def test_colors_on_terminal(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            text = style.paint("hi", style.AGENT, FakeTty())
        self.assertEqual(text, f"{style.AGENT}hi{style.RESET}")

    def test_plain_when_not_a_terminal(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(style.paint("hi", style.AGENT, io.StringIO()), "hi")

    def test_no_color_and_opt_out(self) -> None:
        for env in ({"NO_COLOR": "1"}, {"MYCLI_COLOR": "0"}):
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(style.paint("hi", style.USER, FakeTty()), "hi")


if __name__ == "__main__":
    unittest.main()
