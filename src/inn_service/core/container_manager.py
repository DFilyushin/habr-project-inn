import asyncio
from abc import ABC, abstractmethod
from typing import Type, List, Callable

from injector import singleton, provider, Injector, Module
from starlette.requests import Request

from core.event_mixins import EventLiveProbeMixin, StartupEventMixin, ShutdownEventMixin
from settings import Settings


class Container(ABC, Module):

    @singleton
    @provider
    @abstractmethod
    def provide_settings(self) -> Settings:
        return Settings()


class ContainerManager:

    def __init__(self, cls_container: Type[Container]) -> None:
        self._container = Injector(cls_container())
        self._bindings = self._container.binder._bindings

    def get_container(self) -> Injector:
        return self._container

    def get_live_probe_handlers(self) -> List[Type[Callable]]:
        """
        Получить список обработчиков реализующих миксину проверка liveness probe EventLiveProbeMixin
        """
        result = []
        binding_collection = [binding for binding in self._bindings]
        for binding in binding_collection:
            if issubclass(binding, EventLiveProbeMixin):
                binding_obj = self._container.get(binding)
                result.append(binding_obj.is_connected)
        return result

    def get_startup_handlers(self):
        handlers = []
        binding_collection = [binding for binding in self._bindings]
        for binding in binding_collection:
            if issubclass(binding, StartupEventMixin):
                binding_obj = self._container.get(binding)
                handlers.append(binding_obj.startup())
        return handlers

    def get_shutdown_handlers(self):
        handlers = []
        binding_collection = [binding for binding in self._bindings]
        for binding in binding_collection:
            if issubclass(binding, ShutdownEventMixin):
                binding_obj = self._container.get(binding)
                handlers.append(binding_obj.shutdown())
        return handlers

    async def run_startup(self) -> None:
        exception = None
        for handler in self.get_startup_handlers():
            if exception:
                handler.close()
            else:
                try:
                    await handler
                except Exception as exc:
                    exception = exc

        if exception is not None:
            raise exception

    async def run_shutdown(self) -> None:
        handlers = []
        for handler in self.get_shutdown_handlers():
            handlers.append(handler)
        await asyncio.gather(*handlers)


async def get_container_injector(request: Request) -> Container:
    return request.app.container
