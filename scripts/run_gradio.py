"""Gradio web interface for HN Agent with clean output.

Hides internal agent reasoning (thoughts, tool calls, observations).
Shows only a progress indicator and the final answer.
"""

import sys
from pathlib import Path
from collections.abc import Generator

sys.path.insert(0, str(Path(__file__).parent.parent))

import gradio as gr
from smolagents import GradioUI
from smolagents.memory import ActionStep, FinalAnswerStep, PlanningStep

from config import get_settings
from hn_agent.core.agent import create_hn_agent
from hn_agent.utils.logger import logger

EXAMPLE_QUESTIONS = [
    "What's trending on Hacker News right now?",
    "Fetch the top 3 stories and explain why they're popular",
    "What are people discussing in the top HN thread?",
    "Give me a quick summary of today's top 5 Hacker News stories",
]

PROGRESS_MESSAGES = ["Thinking...", "Working...", "Checking...", "Finalizing..."]


class HNGradioUI(GradioUI):
    """GradioUI subclass with clean output: no internal steps, just results."""

    def _stream_response(
        self, message: str | dict, history: list[dict]
    ) -> Generator:
        """Stream only progress indicators and the final answer."""
        task, task_files = self._process_message(message)

        all_messages: list[gr.ChatMessage] = []
        step_count = 0

        for event in self.agent.run(
            task,
            images=task_files,
            stream=True,
            reset=self.reset_agent_memory,
            additional_args=None,
        ):
            if isinstance(event, PlanningStep):
                # Show a progress indicator, don't expose the plan
                progress = gr.ChatMessage(
                    role="assistant",
                    content="Thinking...",
                    metadata={"title": "Status"},
                )
                if not all_messages:
                    all_messages.append(progress)
                else:
                    all_messages[0] = progress
                yield all_messages

            elif isinstance(event, ActionStep):
                # Rotate through progress messages per step
                step_count += 1
                label = PROGRESS_MESSAGES[
                    min(step_count, len(PROGRESS_MESSAGES)) - 1
                ]
                progress = gr.ChatMessage(
                    role="assistant",
                    content=label,
                    metadata={"title": "Status"},
                )
                if not all_messages:
                    all_messages.append(progress)
                else:
                    all_messages[0] = progress
                yield all_messages

            elif isinstance(event, FinalAnswerStep):
                # Replace everything with the final answer
                output = event.output
                if hasattr(output, "to_string"):
                    content = output.to_string()
                elif not isinstance(output, str):
                    content = str(output)
                else:
                    content = output

                all_messages = [
                    gr.ChatMessage(role="assistant", content=content)
                ]
                yield all_messages

            # Ignore ChatMessageStreamDelta — we don't surface partial tokens

    def create_app(self):
        type_messages_kwarg = (
            {"type": "messages"} if gr.__version__.startswith("5") else {}
        )

        chatbot = gr.Chatbot(
            label="Agent",
            avatar_images=(
                None,
                "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/smolagents/mascot_smol.png",
            ),
            **type_messages_kwarg,
        )

        demo = gr.ChatInterface(
            fn=self._stream_response,
            chatbot=chatbot,
            title="Hacker News Trends Agent",
            description=(
                "Ask me about trending Hacker News threads. "
                "I can fetch top stories, explain why they're popular, "
                "and summarize community discussions."
            ),
            examples=EXAMPLE_QUESTIONS,
            multimodal=self.file_upload_folder is not None,
            save_history=True,
            **type_messages_kwarg,
        )
        return demo


def launch_gradio_ui() -> None:
    """Launch the Gradio web interface for the HN Agent."""
    logger.info("Launching Gradio UI...")

    settings = get_settings()

    agent = create_hn_agent(
        provider=settings.MODEL_PROVIDER,
        model_id=settings.MODEL_ID,
        hf_token=settings.HF_TOKEN,
        openai_api_key=settings.OPENAI_API_KEY,
        gemini_api_key=settings.GEMINI_API_KEY,
        max_steps=settings.MAX_AGENT_STEPS,
    )

    ui = HNGradioUI(agent)

    logger.info(f"Starting on http://localhost:{settings.GRADIO_PORT}")
    ui.launch(
        server_name="0.0.0.0",
        server_port=settings.GRADIO_PORT,
        share=settings.GRADIO_SHARE,
    )


if __name__ == "__main__":
    launch_gradio_ui()
