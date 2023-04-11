from injector import singleton, provider
import logging

from core.container_manager import Container
from settings import Settings
from logger import AppLogger
from connection_managers.rabbitmq_connection_manager import RabbitConnectionManager
from connection_managers.mongo_connection_manager import MongoConnectionManager
from services.inn_service import InnService
from services.live_probe_service import LiveProbeService
from infrastructure.queue_manager.queue_manager import QueueManager
from infrastructure.handlers.request_handler import RequestHandler
from clients.inn_nalog_client import NalogApiClient
from repositories.request_mongo_repository import RequestRepository


class ApplicationContainer(Container):

    @singleton
    @provider
    def provide_settings(self) -> Settings:
        return Settings()

    @singleton
    @provider
    def provide_logger(self, settings: Settings) -> AppLogger:
        logger = logging.getLogger(settings.app_name)
        logger.setLevel(logging.DEBUG)
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(sh)
        return AppLogger(logger)

    @singleton
    @provider
    def provide_mongodb_connection(self, settings: Settings, logger: AppLogger) -> MongoConnectionManager:
        return MongoConnectionManager(settings, logger)

    @singleton
    @provider
    def provide_rabbitmq_connection(self, settings: Settings, logger: AppLogger) -> RabbitConnectionManager:
        return RabbitConnectionManager(settings, logger)

    @singleton
    @provider
    def provide_nalog_api_client(self, settings: Settings, logger: AppLogger) -> NalogApiClient:
        return NalogApiClient(settings, logger)

    @singleton
    @provider
    def provide_request_repository(self, settings: Settings, mongo_connection: MongoConnectionManager) -> RequestRepository:
        return RequestRepository(mongo_connection, settings)

    @singleton
    @provider
    def provide_inn_service(
            self,
            settings: Settings,
            logger: AppLogger,
            nalog_api_client: NalogApiClient,
            request_repository: RequestRepository
    ) -> InnService:
        return InnService(settings, logger, nalog_api_client, request_repository)

    @singleton
    @provider
    def provide_queue_manager(
            self,
            settings: Settings,
            logger: AppLogger,
            rabbitmq: RabbitConnectionManager
    ) -> QueueManager:
        return QueueManager(settings, logger, rabbitmq)

    @singleton
    @provider
    def provide_request_handler(
            self,
            settings: Settings,
            logger: AppLogger,
            inn_service: InnService,
            rabbitmq_connection_manager: RabbitConnectionManager
    ) -> RequestHandler:
        return RequestHandler(settings, logger, rabbitmq_connection_manager, inn_service)

    @singleton
    @provider
    def provide_live_probe_service(self, logger: AppLogger) -> LiveProbeService:
        return LiveProbeService(logger)
