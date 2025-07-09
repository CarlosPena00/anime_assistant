from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_JSON = BASE_DIR / "data" / "index" / "chunks.json"
CHROMA_DIR = BASE_DIR / "data" / "index" / "chroma/"
RAW_DIR = BASE_DIR / "data" / "raw"
META_DIR = BASE_DIR / "data" / "metadata"
SUMMARY_DIR = BASE_DIR / "data" / "summaries"

CHUNKS_JSON.parent.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


JIKAN_BASE = "https://api.jikan.moe/v4"
CHUNK_SIZE = 13  # Number of episodes per chunk
