import asyncio
from abc import ABC, abstractmethod
from typing import Type, Tuple, Dict, List, Coroutine, Callable

from injector import singleton, provider, Injector, Module
# from starlette.requests import Request

from inn_service.core.event_mixins import EventSubscriberMixin, EventTypeEnum, EventLiveProbeMixin
from inn_service.settings import Settings


class Container(ABC, Module):

    @singleton
    @provider
    @abstractmethod
    def provide_settings(self) -> Settings:
        return Settings()


class ContainerManager:

    def __init__(self, cls_container: Type[Container]) -> None:
        self.container = Injector(cls_container())
        self.startup_event_collection, self.shutdown_event_collection = self.get_event_collection()

    def get_container(self) -> Injector:
        return self.container

    def get_event_collection(self) -> Tuple[Dict[int, List[Coroutine]], Dict[int, List[Coroutine]]]:
        startup_event_collection = {}
        shutdown_event_collection = {}

        binding_collection = [binding for binding in self.container.binder._bindings]

        for binding in binding_collection:
            if issubclass(binding, EventSubscriberMixin):
                binding_obj = self.container.get(binding)
                subscriber_event_collection = binding_obj.get_subscriber_event_collection()

                for subscriber_event in subscriber_event_collection:
                    if subscriber_event.event == EventTypeEnum.startup:
                        current_collection = startup_event_collection
                    else:
                        current_collection = shutdown_event_collection

                    if subscriber_event.priority not in current_collection:
                        current_collection[subscriber_event.priority] = []

                    current_collection[subscriber_event.priority].append(subscriber_event.handler)

        return startup_event_collection, shutdown_event_collection

    def get_live_probe_handler_collection(self) -> List[Type[Callable]]:
        """
        Получить список обработчиков реализующих миксину проверка liveness probe EventLiveProbeMixin
        """
        result = []
        binding_collection = [binding for binding in self.container.binder._bindings]
        for binding in binding_collection:
            if issubclass(binding, EventLiveProbeMixin):
                binding_obj = self.container.get(binding)
                result.append(binding_obj.is_connected)
        return result

    async def run_startup(self) -> None:
        exception = None
        for _, handlers in sorted(self.startup_event_collection.items()):
            for handler in handlers:
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
        for _, handlers in sorted(self.shutdown_event_collection.items()):
            await asyncio.gather(*handlers)


# async def get_container_injector(request: Request) -> Container:
#     return request.app.container
