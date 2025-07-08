from src.parsers.anime import parse_anime
from src.parsers.anime import parse_episode


def test_parse_episode_minimal():
    raw = {
        "mal_id": 1,
        "title": "Ep1",
        "synopsis": "A test episode.",
        "url": "https://mal/ep/1",
    }
    ep = parse_episode(raw)
    assert ep["episode_id"] == 1
    assert ep["title"] == "Ep1"
    assert ep["synopsis"] == "A test episode."
    assert ep["url"] == "https://mal/ep/1"
    # Optional fields default to None or missing
    assert "aired" not in ep or ep["aired"] is None


def test_parse_episode_full():
    raw = {
        "mal_id": 2,
        "title": "Ep2",
        "synopsis": "Full fields.",
        "url": "https://mal/ep/2",
        "aired": "2022-01-01",
        "score": 8.5,
        "filler": False,
        "recap": False,
        "forum_url": "https://mal/forum/2",
        "title_japanese": "エピソード2",
        "title_romanji": "Episōdo 2",
    }
    ep = parse_episode(raw)
    assert ep["aired"] == "2022-01-01"
    assert ep["score"] == 8.5
    assert ep["filler"] is False
    assert ep["title_japanese"] == "エピソード2"
    assert ep["title_romanji"] == "Episōdo 2"


def test_parse_anime_chunking():
    summary = {
        "mal_id": 100,
        "url": "https://mal/anime/100",
        "title": "Test Anime",
        "synopsis": "Anime synopsis.",
        "score": 7.8,
        "studios": [{"name": "Studio A"}],
        "genres": [{"name": "Comedy"}],
        "aired": {"from": "2022-01-01", "to": "2022-03-01"},
    }
    episodes = [
        {"mal_id": i, "title": f"Ep{i}", "synopsis": f"S{i}", "url": f"u{i}"}
        for i in range(1, 28)
    ]
    data = {"summary": summary, "episodes": episodes}
    chunks = parse_anime(data, max_episodes_per_chunk=13)
    assert len(chunks) == 3  # 27 episodes -> 3 chunks
    assert all(isinstance(c, dict) for c in chunks)
    assert all("episodes" in c for c in chunks)
    assert len(chunks[0]["episodes"]) == 13
    assert len(chunks[1]["episodes"]) == 13
    assert len(chunks[2]["episodes"]) == 1
    # Check metadata propagation
    assert chunks[0]["mal_id"] == 100
    assert chunks[0]["title"] == "Test Anime"
    assert chunks[0]["score"] == 7.8
    assert chunks[0]["studios"] == ["Studio A"]
    assert chunks[0]["genres"] == ["Comedy"]
    assert chunks[0]["aired_from"] == "2022-01-01"
    assert chunks[0]["aired_to"] == "2022-03-01"
