import unittest

from mycli_plus.config import Settings
from mycli_plus.session import ChatSession


class ChatSessionTests(unittest.TestCase):
    def test_trims_oversized_tool_turn_to_user_and_final_answer(self) -> None:
        session = ChatSession(Settings(api_key="test"), max_history=3)
        session.messages.extend(
            [
                {"role": "user", "content": "Do a complex task"},
                {"role": "assistant", "content": "", "tool_calls": [{"id": "call-1"}]},
                {"role": "tool", "tool_call_id": "call-1", "content": "intermediate"},
                {"role": "assistant", "content": "Done"},
            ]
        )

        session._trim_history("Done")

        self.assertEqual(len(session.messages), 3)
        self.assertEqual(session.messages[1]["role"], "user")
        self.assertEqual(session.messages[2], {"role": "assistant", "content": "Done"})

    def test_trims_old_turns_at_user_boundary(self) -> None:
        session = ChatSession(Settings(api_key="test"), max_history=3)
        session.messages.extend(
            [
                {"role": "user", "content": "Old question"},
                {"role": "assistant", "content": "Old answer"},
                {"role": "user", "content": "Recent question"},
                {"role": "assistant", "content": "Recent answer"},
            ]
        )

        session._trim_history("Recent answer")

        self.assertEqual(
            session.messages,
            [
                session.system_prompt,
                {"role": "user", "content": "Recent question"},
                {"role": "assistant", "content": "Recent answer"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
