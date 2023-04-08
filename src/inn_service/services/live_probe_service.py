import asyncio
from typing import List, Callable
from logger import AppLogger


class LiveProbeService:
    def __init__(
            self,
            logger: AppLogger
    ):
        self.logger = logger
        self.handlers: List[Callable] = []

    def add_component(self, component: Callable) -> None:
        self.handlers.append(component)

    async def get_component_status(self) -> bool:
        tasks = []
        component_status = True
        for handler in self.handlers:
            tasks.append(handler())
        probe_results = await asyncio.gather(*tasks)

        for probe_result in probe_results:
            component_status = component_status and probe_result.status
            if not probe_result.status:
                self.logger.error(f'Service {probe_result.service_name} is down')

        return component_status
