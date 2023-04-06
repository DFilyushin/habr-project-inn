from typing import Iterable, Optional

from bson import ObjectId
from pymongo import ASCENDING

from inn_service.repositories.base_mongo_repository import BaseRepository
from inn_service.connection_managers.mongo_connection_manager import MongoConnectionManager
from repositories.base_mongo_repository import IndexDef
from inn_service.models.model import RequestModel
from settings import Settings


class RequestRepository(BaseRepository):

    def __init__(self, connection_manager: MongoConnectionManager, settings: Settings):
        super().__init__(connection_manager, settings)

    @property
    def collection_name(self) -> str:
        return 'request'

    @property
    def collection_indexes(self) -> Iterable[IndexDef]:
        return [
            IndexDef(name='passport_num', sort=ASCENDING),
            IndexDef(name='request_id', sort=ASCENDING),
        ]

    async def save_task(self, request: RequestModel) -> str:
        task_id = await self.save_data(request.dict())
        return str(task_id)

    async def get_request_by_id(self, request_id: str) -> Optional[RequestModel]:
        criteria = {'_id': ObjectId(request_id)}
        result = await self.get_data(criteria)
        if result:
            return RequestModel(**result)

    async def update_request(self, request_id: str, replacement_data: dict) -> None:
        await self.update_data(
            {
                '_id': ObjectId(request_id)
            },
            replacement_data
        )


