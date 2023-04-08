from fastapi.responses import Response
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

from infrastructure.controllers.base_controller import BaseController
from services.live_probe_service import LiveProbeService

router = InferringRouter()


@cbv(router)
class CoreController(BaseController):

    def __init__(self):
        self.live_probe_service = self.injector.get(LiveProbeService)

    @router.get('/livez')
    async def check_health(self):
        is_success = await self.live_probe_service.get_component_status()
        status_code = 200 if is_success else 500
        return Response(status_code=status_code)
