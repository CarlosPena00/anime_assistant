import time
from pathlib import Path
from typing import Any

import requests
import requests_cache
from bs4 import BeautifulSoup
from loguru import logger

from src.utils import save_data

requests_cache.install_cache("data/mal_cache", backend="sqlite", expire_after=86400)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
META_DIR = BASE_DIR / "data" / "metadata"
SUMMARY_DIR = BASE_DIR / "data" / "summaries"

META_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


JIKAN_BASE = "https://api.jikan.moe/v4"


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


def _extract_synopsis_from_mal(html: str) -> str | None:
    """Extracts the synopsis block following <h2>Synopsis</h2>."""
    soup = BeautifulSoup(html, "html.parser")

    try:
        header = soup.find("h2", string=lambda t: t and "Synopsis" in t)
        if not header:
            logger.warning("Synopsis header not found")
            return None
        synopsis_div = header.find_parent("div")
        if synopsis_div:
            header.extract()
            synopsis_text = synopsis_div.get_text(separator=" ", strip=True)
            return synopsis_text or None

        logger.warning("No parent div found for synopsis header")
        return None

    except Exception:
        logger.exception("Error parsing synopsis HTML")
        return None


def fetch_episode_synopsis(episode_url: str) -> str | None:
    """Fetches the synopsis of a specific anime episode by scraping HTML.

    Args:
        episode_url: URL of the specific anime episode page.

    Returns:
        The cleaned synopsis string if found, otherwise None.
    """
    if not episode_url:
        return None
    logger.info(f"[+] Fetching episode synopsis from: {episode_url}")
    try:
        resp = requests.get(episode_url, timeout=10)
    except requests.RequestException as e:
        logger.error("Network error fetching episode {exc}", exc=str(e))
        return None
    if resp.status_code != 200:
        logger.warning(
            f"Failed to fetch episode {episode_url} — "
            f"Status {resp.status_code}: {resp.reason}: {resp.text}",
        )
        return None

    synopsis = _extract_synopsis_from_mal(resp.text)
    if not synopsis:
        logger.info(f"No synopsis found for episode at {episode_url}")
        return None
    return synopsis


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
        for ep in data["data"]:
            synopsis = fetch_episode_synopsis(ep["url"])
            ep["synopsis"] = synopsis
            time.sleep(0.1)  # Avoid hitting API too fast
        episodes.extend(data["data"])
        if not data.get("pagination", {}).get("has_next_page"):
            break
        page += 1
    return episodes


def ingest_anime_metadata(query: str) -> list[int]:
    """
    Ingest anime metadata from MyAnimeList based on a search query.
    Fetches metadata, filters it, retrieves episode data, and saves it to files.

    Args:
        query (str): The search query for anime titles.

    Returns:
        list[int]: List of MyAnimeList IDs for the ingested anime.
    """
    logger.info(f"[+] Ingesting anime metadata for query: {query}")
    if not query:
        logger.warning("No query provided for anime metadata ingestion.")
        return []

    animes_data = fetch_metadata_from_myanimelist(query)
    animes_data = filter_anime_metadata(animes_data)
    for anime in animes_data:
        mal_id = anime["mal_id"]
        episodes = fetch_episodes(mal_id)
        data = {"summary": anime, "episodes": episodes}
        save_data(file_path=META_DIR / f"{mal_id}.json", data=data)
    return [a["mal_id"] for a in animes_data]
