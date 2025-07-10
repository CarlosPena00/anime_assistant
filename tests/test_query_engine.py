from unittest.mock import MagicMock
from unittest.mock import patch

from src.query_engine import init_model


@patch("src.query_engine.logger")
@patch("src.query_engine.build_and_persist_vector_index")
@patch("src.query_engine.Groq")
@patch("src.query_engine.Memory")
@patch("src.query_engine.settings")
def test_init_model_creates_chat_engine(
    mock_settings, mock_memory, mock_groq, mock_build_index, mock_logger
):
    # Arrange
    mock_index = MagicMock()
    mock_chat_engine = MagicMock()
    mock_index.as_chat_engine.return_value = mock_chat_engine
    mock_build_index.return_value = mock_index

    mock_llm = MagicMock()
    mock_groq.return_value = mock_llm

    mock_memory = MagicMock()
    mock_memory.return_value = mock_memory

    mock_settings.GROQ_API = "fake-api-key"

    # Act
    result = init_model()

    # Assert
    mock_logger.info.assert_any_call("Start Model Init")
    mock_build_index.assert_called_once()
    mock_groq.assert_called_once()
    mock_index.as_chat_engine.assert_called_once()
    mock_logger.info.assert_any_call("Model loaded!")
    assert result == mock_chat_engine
