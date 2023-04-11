from typing import Iterable, Optional

from pymongo import ASCENDING

from repositories.base_mongo_repository import BaseRepository
from connection_managers.mongo_connection_manager import MongoConnectionManager
from repositories.base_mongo_repository import IndexDef
from models.model import RequestModel
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

    async def save_request(self, request: RequestModel) -> str:
        record_id = await self.save_document(request.dict())
        return str(record_id)

    async def find_request(self, passport_num: str, request_id: str) -> Optional[RequestModel]:
        criteria = {
            '$or': [
                {'passport_num': passport_num},
                {'request_id': request_id}
            ]
        }
        result = await self.get_one_document(criteria)
        if result:
            return RequestModel(**result)

    async def update_request(self, request_id: str, replacement_data: dict) -> None:
        await self.update_document(
            {
                'request_id': request_id
            },
            replacement_data
        )
