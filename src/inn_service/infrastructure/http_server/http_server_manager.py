from typing import Optional

from fastapi import FastAPI
from injector import Injector
from uvicorn import Server, Config

from services.live_probe_service import LiveProbeService
from settings import Settings
from infrastructure.controllers.liveprobe_controller import router as infrastructure_route


class ServerApplication(FastAPI):

    def __init__(self, container: Injector) -> None:
        self.container = container
        settings_ = self.container.get(Settings)
        super(ServerApplication, self).__init__(title=settings_.app_name)
        self.live_probe_service = self.container.get(LiveProbeService)
        self._include_routes()

    def _include_routes(self) -> None:
        self.include_router(infrastructure_route, tags=['Core'])


class ServerAPIManager:

    def __init__(self, container: Injector) -> None:
        self.container = container
        settings = self.container.get(Settings)
        self.host = settings.http_host
        self.port = settings.http_port
        self.http_handler = settings.http_handler
        self.api_server: Optional[Server] = None
        self.api_application = None

        self.init_api_server()

    async def serve(self) -> None:
        await self.api_server.serve()

    async def shutdown_server(self):
        if self.api_server and self.api_server.started:
            await self.api_server.shutdown()

    def init_api_server(self) -> None:
        self.api_application = ServerApplication(self.container)
        config = Config(
            app=self.api_application,
            loop=self.http_handler,
            host=self.host,
            port=self.port,
            access_log=False,
            log_config=None,
        )
        self.api_server = Server(config)
