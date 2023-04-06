from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'INN service'

    db_mongo_host: str
    db_mongo_port: str
    db_mongo_user: str
    db_mongo_pass: str
    db_mongo_name: str
    db_mongo_rs: Optional[str] = None
    db_mongo_auth: str
    db_mongo_timeout_server_select: int = 5000

    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_user: str
    rabbitmq_pass: str
    rabbitmq_vhost: str
    rabbitmq_exchange_type: str
    rabbitmq_prefetch_count: int
    rabbitmq_source_queue_name: str

    client_nalog_url: str

    @property
    def mongo_dsn(self) -> str:
        mongo_dsn = 'mongodb://{}:{}@{}:{}/{}'.format(
            self.db_mongo_user,
            self.db_mongo_pass,
            self.db_mongo_host,
            self.db_mongo_port,
            self.db_mongo_auth
        )

        if self.db_mongo_rs:
            mongo_dsn += f'?replicaSet={self.db_mongo_rs}'

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
