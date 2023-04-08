import json
from typing import Optional, List, Coroutine

from aio_pika import Exchange, connect_robust, Message, Channel
from aio_pika.connection import Connection
from aiormq.exceptions import ChannelPreconditionFailed

from core.event_mixins import EventLiveProbeMixin, LiveProbeStatus, StartupEventMixin, ShutdownEventMixin
from settings import Settings
from logger import AppLogger


class RabbitConnectionManager(StartupEventMixin, ShutdownEventMixin, EventLiveProbeMixin):
    def __init__(self, settings: Settings, logger: AppLogger) -> None:
        self._dsn = settings.rabbitmq_dsn
        self.prefetch_count = settings.rabbitmq_prefetch_count
        self.exchange_type = settings.rabbitmq_exchange_type
        self._connection = None
        self._channel = None
        self._exchange = None
        self.connected: bool = False
        self.logger = logger

    def shutdown(self) -> Coroutine:
        return self.close_connection()

    def startup(self) -> Coroutine:
        return self.create_connection()

    async def create_connection(self) -> None:
        self.logger.info('Create connection RabbitMQ')
        try:
            self._connection = await connect_robust(self._dsn)
            self._connection.reconnect_callbacks.add(self.on_connection_restore)
            self._connection.close_callbacks.add(self.on_close_connection)
            self.connected = True
        except ConnectionError as exc:
            err_message = f'Rabbit connection problem: {exc}'
            self.logger.error(err_message)
            raise ConnectionError(err_message)

    async def close_connection(self) -> None:
        if self._connection:
            await self._connection.close()

    async def get_connection(self) -> Connection:
        return self._connection

    async def get_channel(self) -> Channel:
        if not self._channel:
            connection = await self.get_connection()
            self._channel = await connection.channel()
            await self._channel.set_qos(prefetch_count=self.prefetch_count)
        return self._channel

    async def get_exchange(self) -> Exchange:
        if not self._exchange:
            channel = await self.get_channel()
            self._exchange = await channel.declare_exchange(self.exchange_type, auto_delete=False, durable=True)
        return self._exchange

    async def delete_dl_queue_after_error(self, dl_queue_name: str) -> None:
        connection = await self.get_connection()
        self._channel = await connection.channel()
        channel = await self.get_channel()
        await channel.queue_delete(dl_queue_name)

    async def create_dl_queue(self, queue_name: str, ttl: int):
        channel = await self.get_channel()
        exchange = await self.get_exchange()
        dead_letter_queue_arguments = {
            'x-dead-letter-exchange': exchange.name,
            'x-dead-letter-routing-key': queue_name,
            'x-message-ttl': ttl
        }

        dead_queue = await channel.declare_queue(
            f'dl-{queue_name}',
            auto_delete=False,
            durable=True,
            arguments=dead_letter_queue_arguments
        )
        await dead_queue.bind(exchange)

    async def create_queue_listener(
            self,
            queue_name: str,
            callback_worker,
            use_retry: bool = False,
            retry_ttl: int = 0,
    ) -> None:
        """
        Создание слушателя очереди. При наличии use_retry создаётся очередь с поддержкой dead_letter и
        возможностью переотправки отклонённых
        сообщений.
        @param queue_name: Имя очереди
        @param callback_worker: Функция консьюмера
        @param use_retry: Использование механизма повтора через мёртвые очереди
        @param retry_ttl: Кол-во м/с через которые будет выполнять повтор
        @return: None
        """

        channel = await self.get_channel()
        exchange = await self.get_exchange()

        dl_queue_name = f'dl-{queue_name}'
        queue_arguments = {}

        if use_retry:
            queue_arguments['x-dead-letter-exchange'] = exchange.name
            queue_arguments['x-dead-letter-routing-key'] = dl_queue_name
            try:
                await self.create_dl_queue(queue_name=queue_name, ttl=retry_ttl)
            except ChannelPreconditionFailed:
                self.logger.warning('PRECONDITION_FAILED - trying to reset Dead Letter queue')
                await self.delete_dl_queue_after_error(dl_queue_name=dl_queue_name)
                await self.create_queue_listener(queue_name, callback_worker, use_retry, retry_ttl)
                self.logger.info(f'Dead Letter queue <{dl_queue_name}> recreated')
                return

        queue = await channel.declare_queue(queue_name, auto_delete=False, durable=True, arguments=queue_arguments)
        await queue.bind(exchange)
        await queue.consume(callback_worker)

    async def declare_queue(
            self,
            name: str,
            dead_exchange: Optional[str] = None,
            dead_queue_name: Optional[str] = None
    ) -> None:
        if dead_queue_name:
            queue_arguments = {
                'x-dead-letter-exchange': dead_exchange,
                'x-dead-letter-routing-key': dead_queue_name
            }
        else:
            queue_arguments = {}
        connection = await self.get_connection()
        channel = await connection.channel()
        exchange = await self.get_exchange()
        queue = await channel.declare_queue(name, auto_delete=False, durable=True, arguments=queue_arguments)
        await queue.bind(exchange, name)

    async def send_data_by_queue(self, data: dict, queue_name: str) -> None:
        data_bytes = json.dumps(data).encode()
        exchange = await self.get_exchange()
        self.logger.debug(f'Send message in {queue_name}. Message: {data}')
        await exchange.publish(Message(data_bytes), routing_key=queue_name)

    async def is_connected(self) -> LiveProbeStatus:
        return LiveProbeStatus(service_name='RabbitMQ', status=self.connected)

    def on_close_connection(self, *args):
        self.logger.error('Lost connection to RabbitMQ...')
        self.connected = False

    def on_connection_restore(self, *args):
        self.logger.info('Connection to RabbitMQ has been restored...')
        self._channel = None
        self._exchange = None
        self.connected = True
