from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.prompts.manager import load_prompt


@patch("src.prompts.manager.PROMPT_DIR")
def test_load_prompt_success(mock_prompt_dir):
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.read_text.return_value = "prompt content"
    mock_prompt_dir.__truediv__.return_value = mock_path

    result = load_prompt("v2")

    mock_prompt_dir.__truediv__.assert_called_with("anime_rag_v2.txt")
    assert result == "prompt content"


@patch("src.prompts.manager.PROMPT_DIR")
def test_load_prompt_file_not_found(mock_prompt_dir):
    mock_path = MagicMock()
    mock_path.exists.return_value = False
    mock_prompt_dir.__truediv__.return_value = mock_path

    with pytest.raises(ValueError, match="Prompt version 'missing' not found."):
        load_prompt("missing")


@patch("src.prompts.manager.PROMPT_DIR")
def test_load_prompt_default_version(mock_prompt_dir):
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.read_text.return_value = "default prompt"
    mock_prompt_dir.__truediv__.return_value = mock_path

    result = load_prompt()

    mock_prompt_dir.__truediv__.assert_called_with("anime_rag_v1.txt")
    assert result == "default prompt"
