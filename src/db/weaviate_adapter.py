import random
from enum import Enum
from typing import Any

import weaviate
from faker import Faker
from loguru import logger
from tqdm import tqdm
from weaviate.classes.config import Configure
from weaviate.classes.config import DataType
from weaviate.classes.config import Property
from weaviate.classes.query import Filter
from weaviate.classes.query import Rerank
from weaviate.collections import Collection
from weaviate.collections.classes.internal import QueryReturn

client = weaviate.connect_to_local(port=8079)


class QueryType(Enum):
    """Enumeration of supported Weaviate query strategies."""

    JUST_FILTER = "JUST_FILTER"
    SEMANTIC_SEARCH = "SEMANTIC_SEARCH"
    KEYWORD_BM25_SEARCH = "KEYWORD_BM25_SEARCH"
    HYBRID_SEARCH = "HYBRID_SEARCH"


def generate_fake_documents(n: int = 10) -> list[dict[str, Any]]:
    """
    Generate a list of fake product documents for testing/demo purposes.

    Args:
        n: Number of documents to generate.

    Returns:
        List of dictionaries representing fake products.
    """
    fake = Faker()
    docs = []
    for _ in range(n):
        doc = {
            "pid": fake.uuid4(),
            "name": fake.word(),
            "description": fake.sentence(),
            "price": fake.pyfloat(left_digits=2, right_digits=2, positive=True),
            "category": fake.word(),
            "created_at": fake.iso8601() + "Z",  # requires RFC3339 formatted date
            "user_ratings": random.randint(1, 5),
            "budget": fake.random_element(elements=["Low", "Moderate", "High"]),
        }
        docs.append(doc)
    return docs


def add_objs_to_collection(  # type: ignore[no-any-unimported]
    documents: list[dict[str, Any]],
    collection: weaviate.collections.Collection,
    batch_size: int = 20,
    concurrent_requests: int = 5,
) -> int:
    """
    Adds a list of document objects to a Weaviate collection in batches.

    Args:
        documents (list[dict[str, Any]]): A list of dictionaries, each representing an
            object to be added to the collection.
        collection (weaviate.collections.Collection): The Weaviate collection to which
            the objects will be added.

    Returns:
        None
    """
    if len(documents) == 0:
        return 0

    with collection.batch.fixed_size(
        batch_size=batch_size, concurrent_requests=concurrent_requests
    ) as batch:
        for document in tqdm(documents):
            batch.add_object(properties=document)

    failed_objects = collection.batch.failed_objects
    if failed_objects:
        logger.warning(f"Number of failed imports: {len(failed_objects)}")
        logger.warning(f"First failed object: {failed_objects[0]}")
    return len(documents)


def create_collection(  # type: ignore[no-any-unimported]
    name: str,
    source_properties: list[str],
    properties: list[Property],
    vectorize_collection_name: bool = False,
) -> weaviate.collections.Collection:
    """
    Create a collection in Weaviate if it does not exist.
    If it exists, return the existing collection.

    Args:
        name: The name of the collection to create or retrieve.
        source_properties: List of properties to vectorize. ex: ['place', 'state']
        properties: List of additional properties to define in the collection.
            [
                Property(
                    name="place", vectorize_property_name=True, data_type=DataType.TEXT
                ),
                Property(name="user_ratings", data_type=DataType.NUMBER),
                Property(name="last_updated", data_type=DataType.DATE),
            ]
        vectorize_collection_name: Whether to append the collection name to the text
            to be vectorized.
    Returns:
        The created or existing Weaviate collection.
    """
    if client.collections.exists(name):
        logger.info(f"Collection '{name}' already exists. Returning existing.")
        return client.collections.get(name)

    vector_config = Configure.Vectors.text2vec_transformers(
        name=name,
        source_properties=source_properties,
        vectorize_collection_name=vectorize_collection_name,
    )
    collection = client.collections.create(
        name=name,
        vector_config=vector_config,
        properties=properties,
    )
    return collection


def query_collection(  # type: ignore[no-any-unimported]
    collection: Collection,
    query: str | None = None,
    limit: int = 10,
    filters: Filter | None = None,
    query_type: QueryType = QueryType.SEMANTIC_SEARCH,
    alpha: float = 0.5,
    rerank: Rerank | None = None,
) -> QueryReturn:
    """
    Query a collection in Weaviate.

    Args:
        collection: The Weaviate collection to query.
        query: The query string.
        limit: The maximum number of results to return.
        filters: Filters to apply to the query.
        query_type: The type of query to perform
            (e.g., JUST_FILTER, SEMANTIC_SEARCH, KEYWORD_BM25, HYBRID).
        alpha: The weight of the BM25 score. (HYBRID only)

    Ex:
        filters=Filter.by_property("user_ratings").greater_or_equal(3.5)
        filters=Filter.by_property("budget").contains_any(["Low", "Moderate"])

        response = collection.query.near_text(
            query="I want suggestions to travel during Winter",
            limit=5,
            rerank=Rerank(
                prop="attractions",  # The property to rerank on
                query="Fun places",  # If not provided, the original query will be used
            ),
        )


    Returns:
        A list of dictionaries representing the query results.
    """
    # TODO: Add arize traces/logs
    if not query and query_type != QueryType.JUST_FILTER:
        raise ValueError(f"Query must be provided for {query_type.name}.")

    if query_type == QueryType.JUST_FILTER:
        result = collection.query.fetch_objects(limit=limit, filters=filters)

    if query_type == QueryType.SEMANTIC_SEARCH:
        result = collection.query.near_text(
            query=query, limit=limit, filters=filters, rerank=rerank
        )

    if query_type == QueryType.KEYWORD_BM25_SEARCH:
        result = collection.query.bm25(
            query=query,
            limit=limit,
            filters=filters,
            rerank=rerank,
        )
    if query_type == QueryType.HYBRID_SEARCH:
        result = collection.query.hybrid(
            query=query,
            alpha=alpha,  # x% Vector, 100-x% KW
            limit=limit,
            filters=filters,
            rerank=rerank,
        )
    return result


if __name__ == "__main__":
    products_collection = create_collection(
        name="products",
        source_properties=["name", "description", "category", "price"],
        properties=[
            Property(name="pid", data_type=DataType.UUID, vectorize_property_name=True),
            Property(
                name="name", data_type=DataType.TEXT, vectorize_property_name=True
            ),
            Property(
                name="description",
                data_type=DataType.TEXT,
                vectorize_property_name=True,
            ),
            Property(
                name="price", data_type=DataType.NUMBER, vectorize_property_name=True
            ),
            Property(
                name="category", data_type=DataType.TEXT, vectorize_property_name=True
            ),
            Property(name="created_at", data_type=DataType.DATE),
            Property(name="user_ratings", data_type=DataType.NUMBER),
            Property(
                name="budget", data_type=DataType.TEXT, vectorize_property_name=True
            ),
        ],
        vectorize_collection_name=False,
    )
    docs = generate_fake_documents(30)
    count = len(products_collection)
    logger.info(f"Total documents in collection: {count}")

    add_objs_to_collection(docs, products_collection)
    count = len(products_collection)
    logger.info(f"Total documents in collection: {count}")

    sample = query_collection(
        collection=products_collection,
        query="Smart TV",
        limit=5,
        query_type=QueryType.HYBRID_SEARCH,
    )
    description = [r.properties["description"] for r in sample.objects]
    logger.info(f"Sample documents: {description}")

    client.close()
