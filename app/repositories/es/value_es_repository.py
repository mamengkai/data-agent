from dataclasses import asdict

from elasticsearch import AsyncElasticsearch

from app.entities.value_info import ValueInfo


class ValueESRepository:

    index_name = "value_index"
    index_mapping = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},
            "column_id": {"type": "keyword"}
        }
    }

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def recreate_index(self):
        if await self.client.indices.exists(index=self.index_name):
            await self.client.indices.delete(index=self.index_name)
        await self.client.indices.create(index=self.index_name, mappings=self.index_mapping)

    async def index(self, values_infos: list[ValueInfo], batch_size=20):
        for i in range(0, len(values_infos), batch_size):
            batch_value_infos = values_infos[i: i + batch_size]
            batch_operations = []
            for value_info in batch_value_infos:
                batch_operations.append(
                    {
                        "index": {
                            "_index": self.index_name,
                            "_id": value_info.id,
                        }
                    }
                )
                batch_operations.append(asdict(value_info))
            await self.client.bulk(operations=batch_operations)

