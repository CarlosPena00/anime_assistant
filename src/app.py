from typing import Any

import gradio as gr

from src.query_engine import reset_chat
from src.query_engine import run_rag_chatbot


def parse_chatbot(
    message: str, chat_history: list[dict[str, Any]] | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """
    Gradio uses the first argument of the function as a pre-written text to
    facilitate user interaction. In our case, the run_rag_chatbot function
    returns the last response from the chatbot of the first argument.
    Therefore, we will only use the run_rag_chatbot for the `history` and
    return empty for the pre-written text.
    """
    return "", run_rag_chatbot(message, chat_history)[1]


def create_gradio_app() -> gr.Blocks:  # type: ignore[no-any-unimported]
    with gr.Blocks() as demo:
        gr.Markdown("# Chatbot")
        chatbot = gr.Chatbot(type="messages")
        msg = gr.Textbox(
            label="Type your message here...",
            placeholder="Hello, can you tell me about Naruto?",
        )
        reset = gr.Button("Reset")
        reset.click(reset_chat, None, chatbot, queue=False)
        msg.submit(parse_chatbot, [msg, chatbot], [msg, chatbot])
    return demo


if __name__ == "__main__":
    demo = create_gradio_app()
    demo.launch()
