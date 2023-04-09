import json
from typing import List, Callable

from aio_pika import IncomingMessage
from logger import AppLogger
from pydantic import ValidationError

from connection_managers.rabbitmq_connection_manager import RabbitConnectionManager
from infrastructure.handlers.base_handler import BaseHandler
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
        self._handlers: List[BaseHandler] = []
        self._exchange = None

    def add_handler(self, item: BaseHandler):
        self._handlers.append(item)

    async def run_handlers_async(self) -> None:
        """
        Инициализация обработчиков
        """
        for handler in self._handlers:
            await self._create_consumer(handler)

    async def _create_consumer(self, item: BaseHandler) -> None:
        self.logger.info(f'Create consumer for {item.get_source_queue()}')
        await self.connection_manager.create_queue_listener(
            item.get_source_queue(),
            self.make_consumer_function(item),
            item.get_use_retry(),
            item.get_retry_ttl()
        )

    async def _send_error_response(self, response: dict, queue: str) -> None:
        await self.connection_manager.send_data_in_queue(response, queue)

    def _get_message_retry(self, message: IncomingMessage) -> int:
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
                request_id = data.get('requestId')
                count_retry = self._get_message_retry(message)

                is_processed = await handler.run_handler(data, request_id, result_queue, count_retry)

                if is_processed:
                    await message.ack()
                else:
                    await message.reject()

            except json.JSONDecodeError as exc:
                self.logger.error('Unable to parse message.', details=str(exc), message=message_content)
                await message.ack()

            except ValidationError as exc:
                error_message = f'Request body content error. {str(exc.errors())}'
                self.logger.error(error_message)
                if result_queue:
                    response = handler.get_error_response(request_id, error_message)
                    await self._send_error_response(response, result_queue)
                await message.ack()

            except Exception as ex:
                error_message = f'Handler {handler=} error. Type error: {type(ex)=}, message: {str(ex)}'
                self.logger.error(error_message, reply_to=result_queue, request_id=request_id)
                if result_queue:
                    response = handler.get_error_response(request_id, error_message)
                    await self._send_error_response(response, result_queue)
                await message.ack()

        return _function
