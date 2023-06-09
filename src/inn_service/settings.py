from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'INN service'
    app_request_retry_times: int  # Количество попыток обработки внешнего запроса
    app_request_retry_sec: int  # Время задержки в секундах перед повторной обработкой запроса

    http_host: str
    http_port: int
    http_handler: str = 'asyncio'

    mongo_host: str
    mongo_port: str
    mongo_user: str
    mongo_pass: str
    mongo_name: str
    mongo_rs: Optional[str] = None
    mongo_auth: str
    mongo_timeout_server_select: int = 5000

    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_pass: str
    rabbitmq_vhost: str
    rabbitmq_exchange_type: str
    rabbitmq_prefetch_count: int
    rabbitmq_source_queue_name: str

    client_nalog_url: str  # Адрес внешнего сервиса для получения ИНН
    client_nalog_timeout_sec: int  # Таймаут ожидания ответа от сервиса
    client_nalog_retries: int  # Количество попыток запросов к внешнему сервису
    client_nalog_wait_sec: int  # Время ожидания между попытками client_nalog_retries

    @property
    def mongo_dsn(self) -> str:
        mongo_dsn = 'mongodb://{}:{}@{}:{}/{}'.format(
            self.mongo_user,
            self.mongo_pass,
            self.mongo_host,
            self.mongo_port,
            self.mongo_auth
        )

        if self.mongo_rs:
            mongo_dsn += f'?replicaSet={self.mongo_rs}'

        return mongo_dsn

    @property
    def rabbitmq_dsn(self) -> str:
        return 'amqp://{}:{}@{}:{}/{}'.format(
            self.rabbitmq_user,
            self.rabbitmq_pass,
            self.rabbitmq_host,
            self.rabbitmq_port,
            self.rabbitmq_vhost
        )
