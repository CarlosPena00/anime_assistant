import json
from pathlib import Path
from typing import Any


def save_data(file_path: str | Path, data: dict[str, Any]) -> None:
    """
    Save the provided data as a JSON file to the specified file path.

    Args:
        file_path (str): The path where the JSON file will be saved.
                         file_path example: DIR / f"{process_query}_{page}.json"
        data (dict[str, Any]): The data to be saved. If empty, nothing is written.
    """
    if not data:
        return
    file_path = Path(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)  # Handle Japanese
