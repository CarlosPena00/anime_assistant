from typing import Any

from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.chat_engine.types import BaseChatEngine
from llama_index.core.memory import Memory
from llama_index.llms.groq import Groq
from loguru import logger

from src.constants import GROQ_MODEL_NAME
from src.constants import SIMILARITY_TOP_K
from src.rag_index import build_and_persist_vector_index
from src.settings import settings


def init_model() -> BaseChatEngine:  # type: ignore[no-any-unimported]
    """
    Initializes and configures the anime assistant chat model.

    This function performs the following steps:
    1. Builds and persists a vector index for efficient context retrieval.
    2. Instantiates a language model (LLM) using the Groq API.
    3. Sets up a chat memory buffer to summarize and manage conversation history.
    4. Creates a chat engine that:
        - Uses the vector index for context-aware responses.
        - Applies a system prompt with strict answering rules for anime-related queries.
        - Restricts answers to information present in the provided context.
        - Formats responses in markdown with clear, concise language.

    Returns:
        chat_engine: An instance of the configured chat engine ready to answer
        anime-related questions.
    """
    logger.info("Start Model Init")
    index = build_and_persist_vector_index()
    llm = Groq(model=GROQ_MODEL_NAME, api_key=settings.GROQ_API)
    memory = Memory(llm=llm, token_limit=512)
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        llm=llm,
        memory=memory,
        similarity_top_k=SIMILARITY_TOP_K,
        system_prompt=(
            """
            You are an expert Anime assistant trained to answer user questions using
            retrieved information from MyAnimeList and official anime metadata.
            (over 1000 animes).

            In the first message you need to ask which anime the user is interested in.
            You will then retrieve relevant context from the vector index and use it to
            answer questions about anime titles, episodes, airing dates, and genres.

            === Context ===
            Your task is to answer questions accurately and concisely using the provided
            context, which includes:
            - Anime titles and descriptions
            - Episode names and summaries
            - Airing dates, seasons, and genres

            === Answering Rules ===
            - Use only the information present in the context.
            - If the answer is not clearly stated, say:
                "I'm not sure based on what I found."
            - Be clear and factual. Do not invent characters, scenes, or plot points.
            - If the user asks about a specific episode,
                try to match it by episode number or title.
            - You may refer to characters, episodes, or genres mentioned in the context,
                but do not make assumptions outside of that.
            - Always write in English, even if the question is in another language.

            === Output Format ===
            Answer in markdown with clear formatting, short paragraphs,
                and avoid repetition.
            Add bullet points or numbered lists if multiple facts are relevant.
            ====================
        """
            # TODO: Add examples of questions and answers
        ),
    )
    logger.info("Model loaded!")
    return chat_engine


class ChatEngineManager:
    """
    ChatEngineManager is a singleton-style manager for a chat model instance.

    Class Attributes:
        _model: Holds the singleton instance of the chat model.

    Methods:
        instance():
            Returns the singleton instance of the chat model.
            Initializes the model using `init_model()` if it does not already exist.
    Use:
        chat_engine = ChatEngineManager.instance()
    """

    _model = None

    @classmethod
    def instance(cls) -> BaseChatEngine:  # type: ignore[no-any-unimported]
        if cls._model is None:
            cls._model = init_model()
        return cls._model


def run_rag_chatbot(
    message: str, chat_history: list[dict[str, Any]] | None = None
) -> tuple[str, list[dict[str, Any]]]:
    """
    Runs a Retrieval-Augmented Generation (RAG) chatbot with the provided user message
        and chat history.

    Args:
        message (str): The user's input message to the chatbot.
        chat_history (list[dict[str, Any]] | None, optional):
            The conversation history as a list of message dictionaries.
            Each dictionary should contain at least the keys 'role' and 'content'.
            If None, a new history is started.

        Example chat_history:
        [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': "Hello again! ..."}
        ]

    Returns:
        tuple[str, list[dict[str, Any]]]: A tuple containing:
            - The assistant's response as a string.
            - The updated chat history including the latest user and assistant messages.

    """
    if chat_history is None:
        chat_history = []
    logger.info(f"Chatbot input: {message}")
    chat_engine = ChatEngineManager.instance()
    response = chat_engine.chat(message)
    log_metadata(response)
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": response.response})
    logger.info(f"Chatbot response: {response.response}")
    return response.response, chat_history


def log_metadata(response: AgentChatResponse) -> None:  # type: ignore[no-any-unimported]
    try:
        embedding_logs = [
            r.to_dict()["node"]["metadata"] for r in response.source_nodes
        ]
        for idx, metadata in enumerate(embedding_logs):
            logger.info(
                f"Embedding log {idx:2}: {metadata['score']:0.2f}: "
                f"{metadata['mal_id']=:<7} {metadata['title']=}"
            )
    except:  # noqa: E722
        pass


def reset_chat() -> list[dict[str, Any]]:
    """
    Resets the chat engine to its initial state.
    """
    chat_engine = ChatEngineManager.instance()
    chat_engine.reset()
    return []


if __name__ == "__main__":
    response, history = run_rag_chatbot(
        "Hello, I want to know about Kaguya sama love is war first season?", None
    )
    response, history = run_rag_chatbot(
        "Yes!! I want to know about it, what happen in first episode?", history
    )
    while True:
        response, history = run_rag_chatbot(input("What do you want to ask? "), history)
