import unittest

from mycli_plus.agent import run_agent
from mycli_plus.config import Settings
from mycli_plus.registry import ToolRegistry


class AgentTests(unittest.TestCase):
    def test_tool_call_round_trip(self) -> None:
        registry = ToolRegistry()
        registry.functions["calc"] = lambda expression: "5"
        messages = [{"role": "user", "content": "What is 2 + 3?"}]
        replies = iter(
            [
                {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "function": {
                                "name": "calc",
                                "arguments": '{"expression": "2 + 3"}',
                            },
                        }
                    ],
                },
                {"content": "5", "tool_calls": []},
            ]
        )

        def fake_chat(messages, tools, *, settings):
            return next(replies)

        result = run_agent(
            messages,
            settings=Settings(api_key="test"),
            registry=registry,
            chat_fn=fake_chat,
        )
        self.assertEqual(result, "5")
        self.assertEqual(messages[-2]["role"], "tool")
        self.assertEqual(messages[-2]["content"], "5")

    def test_emits_verbose_events(self) -> None:
        replies = iter(
            [
                {
                    "content": "checking",
                    "tool_calls": [
                        {
                            "id": "c1",
                            "function": {"name": "calc", "arguments": '{"expression": "1+1"}'},
                        }
                    ],
                },
                {"content": "2", "tool_calls": []},
            ]
        )
        events: list[str] = []
        registry = ToolRegistry()
        registry.functions["calc"] = lambda expression: "2"

        run_agent(
            [{"role": "user", "content": "1+1?"}],
            settings=Settings(api_key="test"),
            registry=registry,
            chat_fn=lambda messages, tools, *, settings: next(replies),
            on_event=lambda kind, **data: events.append(kind),
        )

        self.assertEqual(
            events,
            ["model_call", "model_reply", "tool_call", "tool_result", "model_call", "model_reply"],
        )


if __name__ == "__main__":
    unittest.main()
