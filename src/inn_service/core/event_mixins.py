from abc import ABC, abstractmethod
from typing import Coroutine

from pydantic import BaseModel


class LiveProbeStatus(BaseModel):
    service_name: str
    status: bool


class EventLiveProbeMixin(ABC):

    @abstractmethod
    def is_connected(self) -> LiveProbeStatus:
        raise NotImplementedError


class StartupEventMixin(ABC):

    @abstractmethod
    def startup(self) -> Coroutine:
        raise NotImplementedError


class ShutdownEventMixin(ABC):

    @abstractmethod
    def shutdown(self) -> Coroutine:
        raise NotImplementedError
