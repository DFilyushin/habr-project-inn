from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
from pymongo.mongo_client import MongoClient

from inn_service.core.event_mixins import (
    EventLiveProbeMixin,
    LiveProbeStatus,
    EventSubscriberModel,
    EventSubscriberMixin,
    EventTypeEnum,
)
from inn_service.core.exceptions import MongoConnectionError
from inn_service.settings import Settings
from logger import AppLogger


class MongoConnectionManager(EventSubscriberMixin, EventLiveProbeMixin):
    def __init__(self, settings: Settings, logger: AppLogger):
        self.logger = logger
        self._mongodb_uri = settings.mongo_dsn
        self._timeout = settings.db_mongo_timeout_server_select
        self._connection: MongoClient = AsyncIOMotorClient(
            self._mongodb_uri,
            serverSelectionTimeoutMS=self._timeout,
            connect=False
        )

    async def get_connection(self) -> AsyncIOMotorClient:
        is_connected = await self.is_connected()
        if is_connected.status:
            return self._connection
        else:
            await self.create_connection()
            return self._connection

    async def create_connection(self) -> None:
        self.logger.info('Create connection MongoDB')
        try:
            self._connection.is_mongos
        except ServerSelectionTimeoutError as exc:
            raise MongoConnectionError(str(exc))

    async def close_connection(self):
        if self._connection is not None:
            self._connection.close()

    def get_subscriber_event_collection(self) -> List[EventSubscriberModel]:
        return [
            EventSubscriberModel(handler=self.create_connection(), event=EventTypeEnum.startup),
            EventSubscriberModel(handler=self.close_connection(), event=EventTypeEnum.shutdown)
        ]

    async def is_connected(self) -> LiveProbeStatus:
        try:
            self._connection.is_mongos
            status = True
        except ServerSelectionTimeoutError:
            status = False

        return LiveProbeStatus(service_name='MongoDb', status=status)
