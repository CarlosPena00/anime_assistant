from unittest.mock import Mock
from unittest.mock import patch

import pytest
from requests.exceptions import RequestException

from src.ingest import _extract_synopsis_from_mal
from src.ingest import fetch_episode_synopsis
from src.ingest import fetch_metadata_from_myanimelist
from src.ingest import filter_anime_metadata
from src.ingest import ingest_anime_metadata


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


def test_extract_synopsis_from_mal_returns_synopsis():
    html = """
    <div>
        <h2>Synopsis</h2>
        In a world where anime is real, adventures await.
    </div>
    """
    result = _extract_synopsis_from_mal(html)
    assert result == "In a world where anime is real, adventures await."


def test_extract_synopsis_from_mal_no_synopsis_header():
    html = """
    <div>
        <h2>Story</h2>
        This is not a synopsis.
    </div>
    """
    result = _extract_synopsis_from_mal(html)
    assert result is None


def test_extract_synopsis_from_mal_no_parent_div():
    html = """
    <h2>Synopsis</h2>
    This synopsis is not inside a div.
    """
    result = _extract_synopsis_from_mal(html)
    assert result is None


def test_extract_synopsis_from_mal_empty_html():
    html = ""
    result = _extract_synopsis_from_mal(html)
    assert result is None


def test_fetch_episode_synopsis_success():
    html = "<div><h2>Synopsis</h2>Some summary here.</div>"
    mock_resp = Mock(status_code=200, text=html)
    with patch("src.ingest.requests.get", return_value=mock_resp):
        result = fetch_episode_synopsis("http://fake-url")
        assert "Some summary" in result


def test_fetch_episode_synopsis_network_error():
    with patch("src.ingest.requests.get", side_effect=RequestException("fail")):
        assert fetch_episode_synopsis("http://fake-url") is None


def test_fetch_episode_synopsis_no_synopsis():
    html = "<div><h2>Other</h2>No synopsis here.</div>"
    mock_resp = Mock(status_code=200, text=html)
    with patch("src.ingest.requests.get", return_value=mock_resp):
        assert fetch_episode_synopsis("http://fake-url") is None


@patch("src.ingest.requests.get")
@patch("src.ingest.save_data")
def test_fetch_metadata_from_myanimelist_success(mock_save_data, mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"type": "TV", "title": "Show 1"},
            {"type": "Movie", "title": "Movie 2"},
        ]
    }
    mock_get.return_value = mock_response

    result = fetch_metadata_from_myanimelist("Kaguya Sama")
    assert isinstance(result, list)
    assert result[0]["title"] == "Show 1"
    assert result[1]["title"] == "Movie 2"
    assert mock_save_data.called
    mock_get.assert_called_once_with(
        "https://api.jikan.moe/v4/anime", params={"q": "Kaguya Sama", "limit": 20}
    )


@patch("src.ingest.requests.get")
@patch("src.ingest.save_data")
def test_fetch_metadata_from_myanimelist_http_error(mock_save_data, mock_get):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = RequestException("HTTP error")
    mock_get.return_value = mock_response
    with pytest.raises(RequestException):
        fetch_metadata_from_myanimelist("bad query")
    assert mock_save_data.call_count == 0


@patch("src.ingest.save_data")
@patch("src.ingest.fetch_episodes")
@patch("src.ingest.fetch_metadata_from_myanimelist")
def test_ingest_anime_metadata_happy_path(
    mock_fetch_metadata, mock_fetch_episodes, mock_save_data
):
    mock_fetch_metadata.return_value = [
        {"mal_id": 123, "type": "TV", "title": "Show 1"},
        {"mal_id": 456, "type": "Movie", "title": "Movie 2"},
    ]
    mock_fetch_episodes.side_effect = lambda mal_id: [
        {"episode": 1, "synopsis": "Ep1"},
        {"episode": 2, "synopsis": "Ep2"},
    ]

    result = ingest_anime_metadata("Kaguya Sama")
    assert result == [123, 456]
    mock_fetch_metadata.assert_called_once()
    assert mock_fetch_episodes.call_count == 2
    assert mock_save_data.call_count == 2

    called_files = [call.kwargs["file_path"] for call in mock_save_data.call_args_list]
    assert any("123.json" in str(f) for f in called_files)
    assert any("456.json" in str(f) for f in called_files)
