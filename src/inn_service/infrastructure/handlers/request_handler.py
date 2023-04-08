from typing import Optional

from logger import AppLogger

from infrastructure.handlers.base_handler import BaseHandler
from connection_managers.rabbitmq_connection_manager import RabbitConnectionManager
from settings import Settings
from services.inn_service import InnService
from serializers.request_serializer import RequestSerializer


class RequestHandler(BaseHandler):
    def __init__(
            self,
            settings: Settings,
            logger: AppLogger,
            rabbitmq_connection: RabbitConnectionManager,
            service: InnService
    ) -> None:
        super().__init__(settings, logger, rabbitmq_connection)
        self.source_queue_name = self.settings.rabbitmq_source_queue_name
        self.retry_times = self.settings.app_request_retry_times
        self.retry_sec = self.settings.app_request_retry_sec
        self.service = service

    def get_source_queue(self) -> str:
        return self.source_queue_name

    def get_use_retry(self) -> bool:
        return True

    def get_retry_ttl(self) -> int:
        return self.retry_sec

    async def run_handler(
            self,
            message: dict,
            request_id: Optional[str],
            result_queue: Optional[str],
            count_retry: Optional[int] = 0
    ) -> bool:
        if count_retry > self.retry_times:
            self.logger.warning(f'Request {request_id} was rejected by excess attempts {self.retry_times} times')
            return True

        self.logger.info(f'Get request {request_id} for response {result_queue}')

        client_data = RequestSerializer.parse_obj(message)

        response = await self.service.get_client_inn(client_data)

        if result_queue:
            json_message = response.dict()
            await self.rabbitmq_connection.send_data_by_queue(json_message, result_queue)

        return True
