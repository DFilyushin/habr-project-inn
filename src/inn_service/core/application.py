import asyncio
import traceback
from typing import Type
from injector import Injector

from inn_service.connection_managers.rabbitmq_connection_manager import RabbitConnectionManager
from inn_service.core.container_manager import Container, ContainerManager
from inn_service.settings import Settings
from inn_service.logger import AppLogger


class Application:

    def __init__(self, cls_container: Type[Container]) -> None:
        self.loop = asyncio.get_event_loop()
        self.container_manager = ContainerManager(cls_container)
        self.container = self.container_manager.get_container()
        self.settings = self.container.get(Settings)
        self.logger = self.container.get(AppLogger)
        self.app_name = self.settings.app_name

    def run(self) -> None:
        self.logger.info(f'Starting application {self.app_name}')
        try:
            self.loop.run_until_complete(self.container_manager.run_startup())

            # tasks = asyncio.gather(
            #     self.api_server.serve(),
            #     self.queue_manager.run_handlers_async()
            # )
            # self.loop.run_until_complete(tasks)
        except Exception as exception:
            exit(1)
        finally:
            self.loop.run_until_complete(self.container_manager.run_shutdown())

            self.loop.close()
            self.logger.info('Application disabled')
