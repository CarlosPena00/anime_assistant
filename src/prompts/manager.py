from src.constants import PROMPT_DIR


def load_prompt(version: str = "v1") -> str:
    """
    Loads the prompt text for a specified version from the prompt directory.

    Args:
        version (str): The version identifier of the prompt to load. Defaults to "v1".

    Returns:
        str: The contents of the prompt file as a string.

    Raises:
        ValueError: If the prompt file for the specified version does not exist.
    """
    prompt_path = PROMPT_DIR / f"anime_rag_{version}.txt"
    if not prompt_path.exists():
        raise ValueError(f"Prompt version '{version}' not found. {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")
