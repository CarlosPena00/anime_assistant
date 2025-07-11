import base64
import os

from src.settings import settings

os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://cloud.langfuse.com/api/public/otel"

LANGFUSE_AUTH = base64.b64encode(
    f"{settings.LANGFUSE_PUBLIC_KEY}:{settings.LANGFUSE_SECRET_KEY}".encode()
).decode()
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = settings.LANGFUSE_HOST + "/api/public/otel"
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

from langfuse import Langfuse  # noqa: E402, I001
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor  # noqa: E402


langfuse = Langfuse(
    secret_key=settings.LANGFUSE_SECRET_KEY,
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    host=settings.LANGFUSE_HOST,
)
LlamaIndexInstrumentor().instrument(langfuse=langfuse)
