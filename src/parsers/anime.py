from typing import Any

from src.models.anime import AnimeChunk
from src.models.anime import Episode


def parse_episode(ep: dict[str, Any]) -> Episode:
    return Episode(
        episode_id=ep["mal_id"],
        title=ep["title"],
        synopsis=ep.get("synopsis", ""),
        url=ep["url"],
        aired=ep.get("aired"),
        score=ep.get("score"),
        filler=ep.get("filler"),
        recap=ep.get("recap"),
        forum_url=ep.get("forum_url"),
        title_japanese=ep.get("title_japanese"),
        title_romanji=ep.get("title_romanji"),
    )


def parse_anime(
    data: dict[str, Any], max_episodes_per_chunk: int = 13
) -> list[AnimeChunk]:
    summary = data["summary"]
    episodes_raw = data.get("episodes", [])
    episodes: list[Episode] = [parse_episode(ep) for ep in episodes_raw]
    episode_batches: list[list[Episode]] = [
        episodes[i : i + max_episodes_per_chunk]
        for i in range(0, len(episodes), max_episodes_per_chunk)
    ]
    return [
        AnimeChunk(
            mal_id=summary["mal_id"],
            url=summary["url"],
            title=summary["title"],
            synopsis=summary.get("synopsis"),
            title_english=summary.get("title_english"),
            title_japanese=summary.get("title_japanese"),
            title_synonyms=summary.get("title_synonyms", []),
            score=summary.get("score"),
            scored_by=summary.get("scored_by"),
            rank=summary.get("rank"),
            popularity=summary.get("popularity"),
            members=summary.get("members"),
            favorites=summary.get("favorites"),
            season=summary.get("season"),
            year=summary.get("year"),
            status=summary.get("status"),
            duration=summary.get("duration"),
            rating=summary.get("rating"),
            type=summary.get("type"),
            source=summary.get("source"),
            studios=[s["name"] for s in summary.get("studios", [])],
            genres=[g["name"] for g in summary.get("genres", [])],
            explicit_genres=[g["name"] for g in summary.get("explicit_genres", [])],
            themes=[t["name"] for t in summary.get("themes", [])],
            demographics=[d["name"] for d in summary.get("demographics", [])],
            aired_from=summary.get("aired", {}).get("from"),
            aired_to=summary.get("aired", {}).get("to"),
            episodes=episodes_batch,
        )
        for episodes_batch in episode_batches
    ]
