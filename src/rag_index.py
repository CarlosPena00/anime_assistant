import json
from pathlib import Path
from typing import Any

from llama_index.core import Document

from src.models.anime import AnimeChunk

CHUNKS_JSON = Path("data/index/chunks.json")
CHROMA_DIR = Path("data/index/chroma/")
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_JSON.parent.mkdir(parents=True, exist_ok=True)


def build_documents(chunks: list[AnimeChunk]) -> list[Document]:  # type: ignore[no-any-unimported]
    """
    Converts a list of AnimeChunk objects into a list of Document objects,
    formatting each anime's metadata and episodes into a structured text.

    Args:
        chunks (list[AnimeChunk]): A list of AnimeChunk objects, where each chunk
                                   contains anime metadata and a list of episodes.

    Returns:
        list[Document]: A list of Document objects, each containing the formatted text
                        and associated metadata for an anime.
    """
    docs = []
    for chunk in chunks:
        episode_texts = [
            f"Episode {ep['episode_id']}: {ep['title']}\n{ep.get('synopsis', '')}"
            for ep in chunk["episodes"]
        ]
        text = (
            f"Anime: {chunk['title']} (ID: {chunk['mal_id']})\n"
            f"Synopsis: {chunk.get('synopsis', '')}\n"
            f"Episodes:\n" + "\n\n".join(episode_texts)
        )
        doc = Document(text=text, metadata=chunk)
        docs.append(doc)
    return docs


def load_metadata_files(metadata_dir: Path) -> list[dict[str, Any]]:
    """
    Loads all JSON metadata files from the specified directory.

    Args:
        metadata_dir (Path): The directory containing JSON metadata files.

    Returns:
        list[dict[str, Any]]: A list of dictionaries, each representing the contents
                              of a JSON metadata file.
    """
    files = list(metadata_dir.glob("*.json"))
    anime_objs = []
    for file in files:
        with open(file, encoding="utf-8") as f:
            anime_objs.append(json.load(f))
    return anime_objs
