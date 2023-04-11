from fastapi import Depends
from injector import Injector

from core.container_manager import get_container_injector


class BaseController:
    injector: Injector = Depends(get_container_injector)
