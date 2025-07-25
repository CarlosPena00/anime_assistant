from unittest.mock import MagicMock
from unittest.mock import create_autospec

import pytest
from weaviate.classes.query import Rerank
from weaviate.collections import Collection

from src.db.weaviate_adapter import QueryType
from src.db.weaviate_adapter import add_objs_to_collection
from src.db.weaviate_adapter import query_collection


@pytest.fixture
def mock_collection():
    mock = create_autospec(Collection)
    mock_query = MagicMock()
    mock_query.fetch_objects = MagicMock(return_value=[{"id": 1}])
    mock_query.near_text = MagicMock(return_value=[{"id": 2}])
    mock_query.bm25 = MagicMock(return_value=[{"id": 3}])
    mock_query.hybrid = MagicMock(return_value=[{"id": 4}])
    mock.query = mock_query
    return mock


def test_query_collection_just_filter(mock_collection):
    result = query_collection(
        collection=mock_collection,
        query_type=QueryType.JUST_FILTER,
        limit=5,
        filters=None,
    )
    mock_collection.query.fetch_objects.assert_called_once_with(limit=5, filters=None)
    assert result == [{"id": 1}]


def test_query_collection_semantic_search(mock_collection):
    result = query_collection(
        collection=mock_collection,
        query="test query",
        query_type=QueryType.SEMANTIC_SEARCH,
        limit=3,
        filters=None,
    )
    mock_collection.query.near_text.assert_called_once_with(
        query="test query", limit=3, filters=None, rerank=None
    )
    assert result == [{"id": 2}]


def test_query_collection_semantic_search_no_query_raises(mock_collection):
    with pytest.raises(ValueError, match="Query must be provided for SEMANTIC_SEARCH."):
        query_collection(
            collection=mock_collection,
            query=None,
            query_type=QueryType.SEMANTIC_SEARCH,
        )


def test_query_collection_keyword_bm25(mock_collection):
    result = query_collection(
        collection=mock_collection,
        query="bm25 query",
        query_type=QueryType.KEYWORD_BM25_SEARCH,
        limit=2,
        filters=None,
    )
    mock_collection.query.bm25.assert_called_once_with(
        query="bm25 query", limit=2, filters=None, rerank=None
    )
    assert result == [{"id": 3}]


def test_query_collection_keyword_bm25_no_query_raises(mock_collection):
    with pytest.raises(
        ValueError, match="Query must be provided for KEYWORD_BM25_SEARCH."
    ):
        query_collection(
            collection=mock_collection,
            query=None,
            query_type=QueryType.KEYWORD_BM25_SEARCH,
        )


def test_query_collection_hybrid(mock_collection):
    result = query_collection(
        collection=mock_collection,
        query="hybrid query",
        query_type=QueryType.HYBRID_SEARCH,
        limit=4,
        filters=None,
        alpha=0.7,
    )
    mock_collection.query.hybrid.assert_called_once_with(
        query="hybrid query", alpha=0.7, limit=4, filters=None, rerank=None
    )
    assert result == [{"id": 4}]


def test_query_collection_hybrid_no_query_raises(mock_collection):
    with pytest.raises(ValueError, match="Query must be provided for HYBRID_SEARCH."):
        query_collection(
            collection=mock_collection,
            query=None,
            query_type=QueryType.HYBRID_SEARCH,
        )


def test_query_collection_with_rerank(mock_collection):
    rerank = MagicMock(spec=Rerank)
    query_collection(
        collection=mock_collection,
        query="rerank query",
        query_type=QueryType.SEMANTIC_SEARCH,
        limit=1,
        filters=None,
        rerank=rerank,
    )
    mock_collection.query.near_text.assert_called_once_with(
        query="rerank query", limit=1, filters=None, rerank=rerank
    )


@pytest.fixture
def mock_collection_with_batch():
    mock_collection = MagicMock()
    mock_batch_manager = MagicMock()
    mock_batch_context = MagicMock()
    mock_batch_manager.fixed_size.return_value.__enter__.return_value = (
        mock_batch_context
    )
    mock_collection.batch = mock_batch_manager
    mock_collection.batch.failed_objects = []
    return mock_collection, mock_batch_manager, mock_batch_context


def test_add_objs_to_collection_empty_list(mock_collection_with_batch):
    mock_collection, _, _ = mock_collection_with_batch
    result = add_objs_to_collection([], mock_collection)
    assert result == 0


def test_add_objs_to_collection_adds_all_documents(mock_collection_with_batch):
    mock_collection, mock_batch_manager, mock_batch_context = mock_collection_with_batch
    docs = [{"a": 1}, {"b": 2}, {"c": 3}]
    result = add_objs_to_collection(
        docs, mock_collection, batch_size=2, concurrent_requests=1
    )
    mock_batch_manager.fixed_size.assert_called_once_with(
        batch_size=2, concurrent_requests=1
    )
    assert mock_batch_context.add_object.call_count == 3
    for doc in docs:
        mock_batch_context.add_object.assert_any_call(properties=doc)
    assert result == 3
