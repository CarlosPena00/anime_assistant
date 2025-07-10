import json
from pathlib import Path
from time import time
from typing import Any

import chromadb
from llama_index.core import Document
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.core.storage import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from loguru import logger

from src.constants import CHROMA_DIR
from src.constants import CHUNK_SIZE
from src.constants import CHUNKS_JSON
from src.constants import EMBEDDING_MODEL_NAME
from src.ingest import META_DIR
from src.models.anime import AnimeChunk
from src.parsers.anime import parse_anime


class ChromaEmbeddingWrapper:
    def __init__(self, model_name: str) -> None:
        self.model = HuggingFaceEmbedding(model_name=model_name)

    def __call__(self, input: str) -> Any:
        return self.model.embed(input)

    def name(self) -> Any:
        return self.model.model_name


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
            f"Score {ep.get('score', 'unknown')}; Episode {ep['episode_id']}: "
            f"{ep['title']}\n{ep.get('synopsis', '')}"
            for ep in chunk["episodes"]
        ]
        text = (
            f"Anime: {chunk['title']} (ID: {chunk['mal_id']})\n"
            f"Synopsis: {chunk.get('synopsis', '')}\n"
            f"Episodes:\n" + "\n\n".join(episode_texts)
        )
        metadata: dict[str, Any] = chunk.copy()  # type: ignore[assignment]
        metadata.pop("episodes")
        doc = Document(text=text, metadata=metadata)
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


def load_or_create_chunks() -> list[AnimeChunk]:
    """
    Loads or creates anime chunks from metadata files.

    If the CHUNKS_JSON file exists, it loads the chunks from that file.
    Otherwise, it loads metadata files from META_DIR, parses them into chunks,
    and saves the chunks to CHUNKS_JSON for future use.

    Returns:
        list[AnimeChunk]: A list of AnimeChunk objects containing parsed anime data.
    """
    all_chunks: list[AnimeChunk]
    if CHUNKS_JSON.exists():
        with open(CHUNKS_JSON, encoding="utf-8") as f:
            all_chunks = json.load(f)
    else:
        anime_objs = load_metadata_files(META_DIR)
        all_chunks = []
        for anime in anime_objs:
            all_chunks.extend(parse_anime(anime, max_episodes_per_chunk=CHUNK_SIZE))
        with open(CHUNKS_JSON, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    return all_chunks


def build_and_persist_vector_index() -> VectorStoreIndex:  # type: ignore[no-any-unimported]
    """
    Build and persists a vector index of anime documents.

    Loads or creates anime chunks, builds LlamaIndex documents, sets up ChromaDB,
    indexes the documents using a HuggingFace embedding model, and persists the index.
    """
    start_time = time()
    logger.info("Loading or creating anime chunks...")
    all_chunks = load_or_create_chunks()
    logger.info(f"Loaded {len(all_chunks)} chunks in {time() - start_time:.2f}s.")

    logger.info("Building LlamaIndex documents...")
    docs = build_documents(all_chunks)
    logger.info(f"Built {len(docs)} documents.")

    logger.info("Setting up ChromaDB persistent client and collection...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL_NAME)
    embed_model_ch = ChromaEmbeddingWrapper(model_name=EMBEDDING_MODEL_NAME)

    logger.info(f"Using embedding model: {embed_model.model_name}")
    chroma_collection = chroma_client.get_or_create_collection(
        name="anime", embedding_function=embed_model_ch
    )
    logger.info(f"ChromaDB collection '{chroma_collection.name}' created or retrieved.")
    vector_store = ChromaVectorStore(
        chroma_collection=chroma_collection, chroma_client=chroma_client
    )
    logger.info("ChromaVectorStore initialized.")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    logger.info("Indexing documents with HuggingFace embedding model...")
    index = VectorStoreIndex.from_documents(
        docs,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True,
    )
    logger.info("Persist index to disk.")
    index.storage_context.persist(persist_dir=str(CHROMA_DIR))
    logger.info("RAG pipeline completed successfully.")
    return index


if __name__ == "__main__":
    build_and_persist_vector_index()
