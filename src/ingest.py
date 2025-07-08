import json
from pathlib import Path
from typing import Any

import requests
import requests_cache
from loguru import logger

requests_cache.install_cache("data/mal_cache", backend="sqlite", expire_after=86400)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
META_DIR = BASE_DIR / "data" / "metadata"
SUMMARY_DIR = BASE_DIR / "data" / "summaries"

META_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


JIKAN_BASE = "https://api.jikan.moe/v4"


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
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)  # Handle Japanese


def fetch_metadata_from_myanimelist(query: str) -> list[dict[str, Any]]:
    """
    Fetch anime metadata from MyAnimeList (via Jikan API) for a given search query.
    Saves the raw API response to the RAW_DIR for traceability.

    Args:
        query (str): The anime search query string.

    Returns:
        list[dict[str, Any]]: List of anime metadata dictionaries matching the query.
    """
    logger.info(f"[+] Searching MAL: {query:6>}")
    resp = requests.get(f"{JIKAN_BASE}/anime", params={"q": query, "limit": 20})  # type: ignore[arg-type]
    resp.raise_for_status()
    result = resp.json()

    # TODO: Check for pagination: pagination = result["pagination"]
    page = 1
    process_query = query.replace(" ", "-").replace("/", "_")
    save_data(RAW_DIR / f"{process_query}_{page}.json", result)
    animes_data: list[dict[str, Any]] = result["data"]
    return animes_data


def filter_anime_metadata(animes_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Filter a list of anime metadata dictionaries to include only supported types:
    TV, movie, OVA, special, or TV special.

    Args:
        animes_data (list[dict[str, Any]]): List of anime metadata dictionaries.

    Returns:
        list[dict[str, Any]]: Filtered list containing only supported anime types.
    """
    animes_data = [
        r
        for r in animes_data
        if r["type"].lower() in {"tv", "movie", "ova", "special", "tv_special"}
    ]
    return animes_data


def fetch_episodes(mal_id: int) -> list[dict[str, Any]]:
    """
    Fetch all episodes for a given MyAnimeList anime ID using the Jikan API.
    Handles pagination to retrieve all available episodes.

    Args:
        mal_id (int): MyAnimeList anime ID.

    Returns:
        list[dict[str, Any]]: List of episode metadata dictionaries for the anime.
    """
    episodes = []
    page = 1
    while True:
        logger.info(f"[+] Searching MAL Episodes: {mal_id:6} - Page {page:2}")
        url = f"{JIKAN_BASE}/anime/{mal_id}/episodes?page={page}"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("data"):
            break
        episodes.extend(data["data"])
        if not data.get("pagination", {}).get("has_next_page"):
            break
        page += 1
    return episodes
