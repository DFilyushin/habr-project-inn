import asyncio
from typing import Type

from core.container_manager import Container, ContainerManager
from infrastructure.queues.queue_manager import QueueManager
from infrastructure.http_server.http_server_manager import ServerAPIManager
from infrastructure.handlers.request_handler import RequestHandler
from services.live_probe_service import LiveProbeService
from settings import Settings
from logger import AppLogger


class Application:

    def __init__(self, cls_container: Type[Container]) -> None:
        self.loop = asyncio.get_event_loop()
        self.container_manager = ContainerManager(cls_container)
        self.container = self.container_manager.get_container()
        self.settings = self.container.get(Settings)
        self.logger = self.container.get(AppLogger)
        self.live_probe_service = self.container.get(LiveProbeService)
        self.queue_manager = self.container.get(QueueManager)
        self.app_name = self.settings.app_name
        self.http_server = None

    def init_application(self):
        self.http_server = ServerAPIManager(self.container)

        request_handler = self.container.get(RequestHandler)
        self.queue_manager.add_handler(request_handler)

        live_probe_handlers = self.container_manager.get_live_probe_handler_collection()
        for handler in live_probe_handlers:
            self.live_probe_service.add_component(handler)

    def run(self) -> None:
        self.logger.info(f'Starting application {self.app_name}')

        self.init_application()

        try:
            self.loop.run_until_complete(self.container_manager.run_startup())

            tasks = asyncio.gather(
                self.http_server.serve(),
                self.queue_manager.run_handlers_async(),
            )
            self.loop.run_until_complete(tasks)

            self.loop.run_forever()
        except BaseException as exception:
            exit(1)
        finally:
            self.loop.run_until_complete(self.container_manager.run_shutdown())

            self.loop.close()
            self.logger.info('Application disabled')
