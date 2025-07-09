from unittest.mock import MagicMock
from unittest.mock import patch

from src.constants import SIMILARITY_TOP_K
from src.query_engine import load_query_engine


@patch("src.query_engine.HuggingFaceEmbedding")
@patch("src.query_engine.StorageContext")
@patch("src.query_engine.load_index_from_storage")
@patch("src.query_engine.RetrieverQueryEngine")
@patch("src.query_engine.Groq")
@patch("src.query_engine.settings")
@patch("src.query_engine.EMBEDDING_MODEL_NAME", "test-embedding-model")
@patch("src.query_engine.CHROMA_DIR", "/fake/dir")
def test_load_query_engine(
    mock_settings,
    mock_groq,
    mock_retrieverqueryengine,
    mock_load_index_from_storage,
    mock_storagecontext,
    mock_huggingfaceembedding,
):
    mock_embed_model = MagicMock()
    mock_huggingfaceembedding.return_value = mock_embed_model
    mock_storage_context = MagicMock()
    mock_storagecontext.from_defaults.return_value = mock_storage_context
    mock_index = MagicMock()
    mock_load_index_from_storage.return_value = mock_index
    mock_retriever = MagicMock()
    mock_index.as_retriever.return_value = mock_retriever
    mock_llm = MagicMock()
    mock_groq.return_value = mock_llm
    mock_query_engine = MagicMock()
    mock_retrieverqueryengine.from_args.return_value = mock_query_engine
    mock_settings.GROQ_API = "fake-api-key"

    result = load_query_engine()

    mock_huggingfaceembedding.assert_called_once_with(model_name="test-embedding-model")
    mock_storagecontext.from_defaults.assert_called_once_with(persist_dir="/fake/dir")
    mock_load_index_from_storage.assert_called_once_with(
        mock_storage_context, embed_model=mock_embed_model
    )
    mock_index.as_retriever.assert_called_once_with(similarity_top_k=SIMILARITY_TOP_K)
    mock_groq.assert_called_once_with(model="llama3-70b-8192", api_key="fake-api-key")
    mock_retrieverqueryengine.from_args.assert_called_once_with(
        retriever=mock_retriever, llm=mock_llm
    )
    assert result == mock_query_engine
