from typing import Optional, Type

from fintech_logger_core.rabbit_logger import RabbitLogger

from smev_identification.connection_managers.rabbit_connection_manager import RabbitConnectionManager
from smev_identification.handlers.base_handler import BaseHandler
from smev_identification.serializers.client_serializer import CustomerSerializer
from smev_identification.serializers.response_serializer import CodeSerializer, TaskIDResponseSerializer
from smev_identification.services.provider_selection_service import ProviderSelectionService
from smev_identification.repositories.task_repository import TaskRepository
from smev_identification.settings import Settings


class RequestHandler(BaseHandler):
    """
    Обработчик нового внешнего запроса
    """
    def __init__(
            self,
            settings: Settings,
            logger: RabbitLogger,
            rabbit_connection_manager: RabbitConnectionManager,
            serializer: Type[CustomerSerializer],
            service_provider: ProviderSelectionService,
            task_repository: TaskRepository
    ) -> None:
        super().__init__(settings, logger, rabbit_connection_manager, serializer, service_provider, task_repository)
        self.source_queue_name = self.settings.service_rabbitmq_source_queue_name

    def get_source_queue(self) -> str:
        return self.source_queue_name

    def get_use_retry(self) -> bool:
        return False

    def control_header_params(self) -> bool:
        return True

    async def handle_validation_error(self, request_id: str, error_message: str, result_queue: Optional[str] = None):
        self.logger.error(error_message, reply_to=result_queue, message_id=request_id)
        if result_queue:
            error_data = TaskIDResponseSerializer(
                code=CodeSerializer.TASK_NOT_EXISTS,
                request_id=request_id,
                error=error_message
            )
            json_message = error_data.dict()
            await self.rabbit_connection_manager.send_data_by_queue(json_message, result_queue)

    async def run_handler(
            self,
            client: CustomerSerializer,
            request_id: str,
            x_creator_id: str,
            result_queue: Optional[str],
            count_retry: Optional[int] = 0
    ) -> bool:
        self.logger.access(reply_to=result_queue, message_id=request_id)

        next_provider = self.service_provider.get_provider()
        service = self.service_provider.get_service(next_provider)
        response = await service.initialize_task(client, x_creator_id, request_id, result_queue)
        if result_queue:
            json_message = response.dict()
            await self.rabbit_connection_manager.send_data_by_queue(json_message, result_queue)
        return True
