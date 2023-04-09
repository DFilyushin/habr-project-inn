from abc import ABC, abstractmethod
from typing import Optional

from logger import AppLogger


from connection_managers.rabbitmq_connection_manager import RabbitConnectionManager
from settings import Settings


class BaseHandler(ABC):
    """
    Базовый обработчик
    """
    def __init__(
            self,
            settings: Settings,
            logger: AppLogger,
            rabbitmq_connection: RabbitConnectionManager
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.rabbitmq_connection = rabbitmq_connection

    def __repr__(self):
        return self.handler_name()

    def handler_name(self) -> str:
        return 'BaseHandler'

    @abstractmethod
    def get_use_retry(self) -> bool:
        raise NotImplementedError

    def get_retry_ttl(self) -> int:
        return 0

    @abstractmethod
    def get_source_queue(self) -> str:
        raise NotImplementedError

    def convert_seconds_to_mseconds(self, value: int) -> int:
        return value * 1000

    @abstractmethod
    def get_error_response(self, request_id: str, error_message: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def run_handler(
            self,
            message: dict,
            request_id: Optional[str],
            result_queue: Optional[str],
            count_retry: Optional[int] = 0
    ) -> bool:
        raise NotImplementedError
