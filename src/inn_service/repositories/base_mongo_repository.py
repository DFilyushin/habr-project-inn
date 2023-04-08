import asyncio
from dataclasses import dataclass
from typing import Optional, List, Iterable, Coroutine

from connection_managers.mongo_connection_manager import MongoConnectionManager
from core.event_mixins import StartupEventMixin
from settings import Settings


@dataclass
class IndexDef:
    name: str
    sort: int


class BaseRepository(StartupEventMixin):

    def startup(self) -> Coroutine:
        return self.create_indexes()

    def __init__(
            self,
            mongodb_connection_manager: MongoConnectionManager,
            setting: Settings
    ) -> None:
        self.mongodb_connection_manager = mongodb_connection_manager
        self.database = setting.mongo_name

    @property
    def collection_name(self) -> str:
        raise NotImplementedError

    @property
    def collection_indexes(self) -> Iterable[IndexDef]:
        raise NotImplementedError

    async def create_index(self, field_name: str, sort_id: int) -> None:
        """
        Создание индекса в фоне
        """
        connection = await self.mongodb_connection_manager.get_connection()
        collection = connection[self.database][self.collection_name]
        await collection.create_index([(field_name, sort_id), ], background=True)

    async def create_indexes(self) -> None:
        """
        Создание всех необходимых индексов для каждого репозитория
        """
        tasks = []
        for index_item in self.collection_indexes:
            tasks.append(self.create_index(index_item.name, index_item.sort))
        asyncio.ensure_future(asyncio.gather(*tasks))

    async def get_data(self, criteria: dict) -> Optional[dict]:
        connection = await self.mongodb_connection_manager.get_connection()
        collection = connection[self.database][self.collection_name]

        data = await collection.find_one(criteria)

        return data

    async def get_list_data(
            self,
            criteria: dict,
            sort_criteria: Optional[list] = None,
            limit: Optional[int] = 0,
            skip: Optional[int] = 0,
    ) -> List[dict]:
        if not sort_criteria:
            sort_criteria = []
        connection = await self.mongodb_connection_manager.get_connection()
        cursor = connection[self.database][self.collection_name].find(
            criteria,
            limit=limit,
            skip=skip,
            sort=sort_criteria
        )

        result = list()
        async for data in cursor:
            result.append(data)
        return result

    async def save_data(self, data: dict) -> str:
        connection = await self.mongodb_connection_manager.get_connection()
        result = await connection[self.database][self.collection_name].insert_one(data)
        return result.inserted_id

    async def update_data(self, criteria: dict, data: dict) -> None:
        connection = await self.mongodb_connection_manager.get_connection()
        await connection[self.database][self.collection_name].update_one(criteria, {'$set': data})

    async def add_nested_item(self, criteria: dict, data: dict) -> None:
        connection = await self.mongodb_connection_manager.get_connection()
        await connection[self.database][self.collection_name].update_one(criteria, {'$push': data})
