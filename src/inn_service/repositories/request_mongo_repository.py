from typing import Iterable, Optional

from pymongo import ASCENDING

from repositories.base_mongo_repository import BaseRepository
from connection_managers.mongo_connection_manager import MongoConnectionManager
from repositories.base_mongo_repository import IndexDef
from models.model import ClientDataModel
from settings import Settings


class RequestRepository(BaseRepository):

    def __init__(self, connection_manager: MongoConnectionManager, settings: Settings):
        super().__init__(connection_manager, settings)

    @property
    def collection_name(self) -> str:
        return 'clients'

    @property
    def collection_indexes(self) -> Iterable[IndexDef]:
        return [
            IndexDef(name='passport_num', sort=ASCENDING),
            IndexDef(name='request_id', sort=ASCENDING),
        ]

    async def save_client_data(self, request: ClientDataModel) -> str:
        record_id = await self.save_document(request.dict())
        return str(record_id)

    async def find_client_data(self, passport_num: str, request_id: str) -> Optional[ClientDataModel]:
        criteria = {
            '$or': [
                {'passport_num': passport_num},
                {'request_id': request_id}
            ]
        }
        result = await self.get_one_document(criteria)
        if result:
            return ClientDataModel(**result)

    async def update_client_data(self, request_id: str, replacement_data: dict) -> None:
        await self.update_document(
            {
                'request_id': request_id
            },
            replacement_data
        )
