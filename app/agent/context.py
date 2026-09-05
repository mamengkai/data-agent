from typing import TypedDict

from langchain_openai import OpenAIEmbeddings

from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository


class DataAgentContext(TypedDict):
    column_qdrant_repository: ColumnQdrantRepository
    embedding_client: OpenAIEmbeddings