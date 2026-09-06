from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState


class QueryService:
    def __init__(self,
                 meta_mysql_repository,
                 embedding_client_manager,
                 dw_mysql_repository,
                 column_qdrant_repository,
                 metric_qdrant_repository,
                 value_es_repository):
        self.meta_mysql_repository = meta_mysql_repository
        self.embedding_client_manager = embedding_client_manager
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.value_es_repository = value_es_repository

    async def query(self, query: str):
        state = DataAgentState(query=query)
        context = DataAgentContext(column_qdrant_repository=self.column_qdrant_repository,
                                   embedding_client=self.embedding_client_manager.client,
                                   metric_qdrant_repository=self.metric_qdrant_repository,
                                   value_es_repository=self.value_es_repository,
                                   meta_mysql_repository=self.meta_mysql_repository,
                                   dw_mysql_repository=self.dw_mysql_repository)
        async for chunk in graph.astream(input=state, context=context, stream_mode='custom'):
            yield f"data: {chunk}\n\n"
