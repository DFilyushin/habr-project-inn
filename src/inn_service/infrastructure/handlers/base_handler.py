from abc import ABC, abstractmethod
from typing import Type, Optional

from logger import AppLogger
from pydantic import BaseModel

from inn_service.connection_managers.rabbitmq_connection_manager import RabbitConnectionManager
from inn_service.models.model import RequestModel
from inn_service.repositories.request_mongo_repository import RequestRepository
from settings import Settings
from inn_service.services.inn_service import InnService


class RequestHandler:
    """
    Базовый обработчик
    """
    def __init__(self, settings: Settings, logger: AppLogger, service: InnService) -> None:
        self.settings = settings
        self.logger = logger
        self.service = service

    async def run_handler(
            self,
            serializer: BaseModel,
            request_id: Optional[str],
            result_queue: Optional[str],
            count_retry: Optional[int] = 0
    ) -> bool:
        """
        Основной обработчик сообщений
        Должен быть реализован в потомке
        """
        self.logger.debug('')
        raise NotImplementedError
