from injector import singleton, provider
import logging

from inn_service.core.container_manager import Container
from inn_service.settings import Settings
from inn_service.logger import AppLogger
from inn_service.connection_managers.rabbitmq_connection_manager import RabbitConnectionManager
from inn_service.connection_managers.mongo_connection_manager import MongoConnectionManager


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
