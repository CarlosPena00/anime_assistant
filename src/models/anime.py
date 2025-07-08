from typing import NotRequired
from typing import TypedDict


class Episode(TypedDict):
    """Represents a single episode.

    Fields:
        episode_id: Unique MyAnimeList episode ID (1-based index)
        title: Episode title (English or romaji)
        synopsis: Episode synopsis
        url: Canonical MAL episode URL
        aired: ISO 8601 air date
        score: Episode-level score from MyAnimeList
        filler: True if episode is filler
        recap: True if episode is a recap
        forum_url: Link to the MAL episode discussion forum
        title_japanese: Original Japanese title
        title_romanji: Romanized Japanese title

    Example:
    {
      "episode_id": 7,
      "url": "https://myanimelist.net/anime/43608/.../episode/7",
      "title": "Miko Iino Can't Love, Part 1 / Studen...",
      "title_japanese": "伊井野ミコは愛せない①文化...",
      "title_romanji": "Iino Miko wa Aisenai Ichi / Bunkasai wo Kataritai ...",
      "aired": "2022-05-21T00:00:00+00:00",
      "score": 4.38,
      "filler": false,
      "recap": false,
      "forum_url": "https://myanimelist.net/forum/?topicid=2017449",
      "synopsis": "Yu and Miko help the Culture Festival Committee organize..."
    }
    """

    episode_id: int
    title: str
    synopsis: str
    url: str
    aired: NotRequired[str]
    score: NotRequired[float]
    filler: NotRequired[bool]
    recap: NotRequired[bool]
    forum_url: NotRequired[str]
    title_japanese: NotRequired[str]
    title_romanji: NotRequired[str]


class AnimeChunk(TypedDict):
    """Represents a chunk of up to 13 episodes from a single anime,
    bundled with anime-level metadata for RAG indexing.

    Fields:
        mal_id: MyAnimeList anime ID (required)
        url: MAL anime detail page (required)
        title: English or romaji title (required)
        synopsis: Full anime synopsis
        title_english: Official English title
        title_japanese: Original Japanese title
        title_synonyms: List of alternate titles
        score: User rating
        scored_by: Number of users that scored
        rank: MAL global rank
        popularity: MAL popularity index
        members: Number of user list additions
        favorites: Number of favorites
        season: Season name (e.g. "spring")
        year: Release year
        status: Airing status
        duration: Duration per episode (text)
        rating: Age classification (e.g. PG-13)
        type: Media type (TV, Movie, OVA, etc.)
        source: Original source (Manga, Novel, etc.)
        studios: List of animation studios
        genres: List of genre labels
        explicit_genres: List of explicit genre labels
        themes: List of theme labels
        demographics: Target demographic labels
        aired_from: ISO date when airing started
        aired_to: ISO date when airing ended
        episodes: List of up to 13 Episodes
    """

    mal_id: int
    url: str
    title: str
    episodes: list[Episode]

    synopsis: NotRequired[str]
    title_english: NotRequired[str]
    title_japanese: NotRequired[str]
    title_synonyms: NotRequired[list[str]]
    score: NotRequired[float]
    scored_by: NotRequired[int]
    rank: NotRequired[int]
    popularity: NotRequired[int]
    members: NotRequired[int]
    favorites: NotRequired[int]
    season: NotRequired[str]
    year: NotRequired[int]
    status: NotRequired[str]
    duration: NotRequired[str]
    rating: NotRequired[str]
    type: NotRequired[str]
    source: NotRequired[str]
    studios: NotRequired[list[str]]
    genres: NotRequired[list[str]]
    explicit_genres: NotRequired[list[str]]
    themes: NotRequired[list[str]]
    demographics: NotRequired[list[str]]
    aired_from: NotRequired[str]
    aired_to: NotRequired[str]
