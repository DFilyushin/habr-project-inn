from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from enum import Enum
from typing import Any, List

from pydantic import BaseModel, validator


class LiveProbeStatus(BaseModel):
    service_name: str
    status: bool


class EventTypeEnum(str, Enum):
    startup = 'startup'
    shutdown = 'shutdown'


class EventSubscriberModel(BaseModel):
    handler: Any
    event: EventTypeEnum
    priority: int = 100

    @validator('handler')
    def validate_handler(cls, value):
        if iscoroutinefunction(value):
            raise ValueError('The handler should be of the type: "coroutine"')
        return value


class EventLiveProbeMixin(ABC):

    @abstractmethod
    def is_connected(self) -> LiveProbeStatus:
        raise NotImplementedError


class EventSubscriberMixin(ABC):
    HIGH_PRIORITY = 1
    MIDDLE_PRIORITY = 100
    LOW_PRIORITY = 200

    @abstractmethod
    def get_subscriber_event_collection(self) -> List[EventSubscriberModel]:
        raise NotImplementedError
