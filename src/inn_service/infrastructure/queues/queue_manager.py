import asyncio
import json
from typing import List, Callable

from aio_pika import IncomingMessage
from logger import AppLogger
from pydantic import ValidationError

from inn_service.connection_managers.rabbitmq_connection_manager import RabbitConnectionManager
from inn_service.infrastructure.handlers.base_handler import BaseHandler
from settings import Settings


class QueueManager:
    """
    Менеджер mq для получения сообщений
    """

    def __init__(
            self,
            settings: Settings,
            logger: AppLogger,
            queue_connection_manager: RabbitConnectionManager
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.connection_manager = queue_connection_manager
        self.handlers: List[BaseHandler] = []
        self._exchange = None

    def add_handler(self, item: BaseHandler):
        self.handlers.append(item)

    async def run_handlers_async(self) -> None:
        """
        Инициализация обработчиков
        """
        for handler in self.handlers:
            await self._create_consumer(handler)

    async def _create_consumer(self, item: BaseHandler) -> None:
        self.logger.info(f'Create consumer for {item.get_source_queue()}')
        await self.connection_manager.create_queue_listener(
            item.get_source_queue(),
            self.make_consumer_function(item),
            item.get_use_retry(),
            item.get_retry_ttl()
        )

    def get_message_retry(self, message: IncomingMessage) -> int:
        """
        Получить количество повторов пересылки сообщения
        """
        count_retry = 0
        x_death = message.headers.get('x-death', [])
        if len(x_death) > 0:
            count_retry = x_death[0].get('count', 0)
        return count_retry

    def make_consumer_function(self, handler: BaseHandler) -> Callable:
        """
        Создание динамической функции для обработки сообщений из mq
        """

        async def _function(message: IncomingMessage) -> None:
            message_content = message.body.decode('utf-8')
            result_queue = message.reply_to
            request_id = None

            try:
                data = json.loads(message_content)

                request_id = data.get('request_id')

                if handler.control_header_params():  # Контроль заголовков включен?
                    if not request_id:
                        error_message = "Request doesn't contain header fields (x_creator_id or request_id)."
                        self.logger.error(error_message)

                        if result_queue:
                            await handler.handle_validation_error(request_id, error_message, result_queue)

                        await message.ack()
                        return

                serialized_data = handler.serializer(**data)

                count_retry = self.get_message_retry(message)

                result = await handler.run_handler(serialized_data, request_id, result_queue, count_retry)

                if result:
                    await message.ack()
                else:
                    await handler.handle_false_response(serialized_data)
                    await message.reject()

            except json.JSONDecodeError as exc:
                self.logger.error(f'Unable to parse message. Description: "{exc}"')
                await message.ack()

            except ValidationError as exc:
                error_message = f'Request body content error. {str(exc.errors())}'
                self.logger.error(error_message)
                if result_queue:
                    await handler.handle_validation_error(request_id, error_message, result_queue)
                await message.ack()

            except Exception as ex:
                error_message = f'Handler error. {handler=} {type(ex)=} {ex=}'
                self.logger.error(error_message, reply_to=result_queue, message_id=message.message_id)
                if result_queue:
                    await self._send_error_response(request_id, error_message, result_queue)
                await message.ack()

        return _function

    async def _send_error_response(self, request_id: str, error_message: str, queue: str) -> None:
        response_message = {
            'request_id': request_id,
            'error': error_message
        }
        await self.connection_manager.send_data_by_queue(response_message, queue)
