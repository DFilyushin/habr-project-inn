from typing import List, Any, Coroutine

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
from pymongo.mongo_client import MongoClient

from core.event_mixins import EventLiveProbeMixin, LiveProbeStatus, StartupEventMixin, ShutdownEventMixin
from core.exceptions import MongoConnectionError
from settings import Settings
from logger import AppLogger


class MongoConnectionManager(StartupEventMixin, ShutdownEventMixin, EventLiveProbeMixin):

    def __init__(self, settings: Settings, logger: AppLogger):
        self.logger = logger
        self._mongodb_uri = settings.mongo_dsn
        self._mongo_db = settings.mongo_name
        self._timeout = settings.mongo_timeout_server_select
        self._connection: AsyncIOMotorClient = AsyncIOMotorClient(
            self._mongodb_uri,
            serverSelectionTimeoutMS=self._timeout,
            connect=False
        )

    def shutdown(self) -> Coroutine:
        return self.close_connection()

    def startup(self) -> Coroutine:
        return self.create_connection()

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
            db = self._connection.get_database(self._mongo_db)
            await db.list_collection_names()
        except (ServerSelectionTimeoutError, OperationFailure) as exc:
            self.logger.error('Error connected to Mongo', details=str(exc))
            raise MongoConnectionError(str(exc))

    async def close_connection(self):
        if self._connection is not None:
            self._connection.close()

    async def is_connected(self) -> LiveProbeStatus:
        try:
            db = self._connection.get_database(self._mongo_db)
            await db.list_collection_names()
            status = True
        except ServerSelectionTimeoutError:
            status = False

        return LiveProbeStatus(service_name='MongoDb', status=status)
