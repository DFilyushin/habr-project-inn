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
    async def run_handler(
            self,
            message: dict,
            request_id: Optional[str],
            result_queue: Optional[str],
            count_retry: Optional[int] = 0
    ) -> bool:
        raise NotImplementedError
