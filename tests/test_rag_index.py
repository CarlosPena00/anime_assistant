import json
import types

from llama_index.core import Document

from src.rag_index import build_documents
from src.rag_index import load_index
from src.rag_index import load_metadata_files


def make_chunk(mal_id: int = 123) -> dict:
    return {
        "mal_id": mal_id,
        "title": "Test Anime",
        "synopsis": "A test anime synopsis.",
        "episodes": [
            {"episode_id": 1, "title": "Ep1", "synopsis": "First ep."},
            {"episode_id": 2, "title": "Ep2", "synopsis": "Second ep."},
        ],
    }


def test_build_documents_smoke_test():
    chunk = make_chunk()
    docs = build_documents([chunk])
    assert len(docs) == 1
    doc = docs[0]
    assert isinstance(doc, Document)
    # Check text content
    assert "Test Anime" in doc.text
    assert "Ep1" in doc.text
    assert "First ep." in doc.text
    # Check metadata
    assert doc.metadata["mal_id"] == 123
    assert doc.metadata["title"] == "Test Anime"


def test_build_documents_when_two_chunks():
    chunks = [make_chunk(mal_id=1), make_chunk(mal_id=2)]
    docs = build_documents(chunks)
    assert len(docs) == 2
    assert docs[0].metadata["mal_id"] == 1
    assert docs[1].metadata["mal_id"] == 2
    assert "Test Anime" in docs[0].text
    assert "Test Anime" in docs[1].text


def test_load_metadata_files(tmp_path):
    # Create two mock metadata files
    anime1 = {"id": 1, "title": "Anime1"}
    anime2 = {"id": 2, "title": "Anime2"}
    file1 = tmp_path / "1.json"
    file2 = tmp_path / "2.json"
    file1.write_text(json.dumps(anime1), encoding="utf-8")
    file2.write_text(json.dumps(anime2), encoding="utf-8")

    # Call the function
    result = load_metadata_files(tmp_path)
    # Should load both files
    assert isinstance(result, list)
    assert len(result) == 2
    titles = {a["title"] for a in result}
    assert titles == {"Anime1", "Anime2"}


class DummyChromaCollection:
    def __init__(self):
        self.name = "dummy"
        self._calls = []


def test_load_index_logs(monkeypatch, caplog):
    dummy_collection = DummyChromaCollection()

    # Patch ChromaVectorStore and VectorStoreIndex.from_vector_store as before
    monkeypatch.setattr(
        "src.rag_index.ChromaVectorStore", lambda chroma_collection: object()
    )
    monkeypatch.setattr(
        "src.rag_index.VectorStoreIndex.from_vector_store",
        lambda vector_store, embed_model: "dummy_index",
    )

    # Patch logger.info to capture log messages
    logs = []
    monkeypatch.setattr("src.rag_index.logger", types.SimpleNamespace(info=logs.append))

    load_index(dummy_collection)
    assert any("Vector index loaded successfully." in str(msg) for msg in logs)
