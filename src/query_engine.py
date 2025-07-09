from llama_index.core import StorageContext
from llama_index.core import load_index_from_storage
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq

from src.constants import CHROMA_DIR
from src.constants import EMBEDDING_MODEL_NAME
from src.constants import GROQ_MODEL_NAME
from src.constants import SIMILARITY_TOP_K
from src.settings import settings


def load_query_engine() -> RetrieverQueryEngine:  # type: ignore[no-any-unimported]
    """
    Initializes and returns a RetrieverQueryEngine instance configured with embedding,
    storage, retriever, and LLM.

    Returns:
        RetrieverQueryEngine: A query engine set up with a HuggingFace embedding model,
        Chroma storage context, retriever with top-5 similarity,
        and a Groq Llama3-70b-8192 LLM.
    """
    embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL_NAME)
    storage_context = StorageContext.from_defaults(persist_dir=str(CHROMA_DIR))
    index = load_index_from_storage(storage_context, embed_model=embed_model)

    retriever = index.as_retriever(similarity_top_k=SIMILARITY_TOP_K)
    llm = Groq(model=GROQ_MODEL_NAME, api_key=settings.GROQ_API)
    query_engine = RetrieverQueryEngine.from_args(retriever=retriever, llm=llm)
    return query_engine
