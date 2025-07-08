from src.ingest import filter_anime_metadata


def test_filter_anime_metadata_filters_types():
    input_data = [
        {"type": "TV", "title": "Show 1"},
        {"type": "Movie", "title": "Movie 1"},
        {"type": "OVA", "title": "OVA 1"},
        {"type": "Special", "title": "Special 1"},
        {"type": "TV_Special", "title": "TV Special 1"},
        {"type": "Manga", "title": "Manga 1"},
        {"type": "Novel", "title": "Novel 1"},
        {"type": "ONA", "title": "ONA 1"},
    ]
    expected_titles = {"Show 1", "Movie 1", "OVA 1", "Special 1", "TV Special 1"}
    filtered = filter_anime_metadata(input_data)
    filtered_titles = {item["title"] for item in filtered}
    assert filtered_titles == expected_titles


def test_filter_anime_metadata_empty():
    assert filter_anime_metadata([]) == []
