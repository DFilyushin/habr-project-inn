import http
from logger import AppLogger
from typing import Optional

import aiohttp

from clients.utils import retry
from core.exceptions import NalogApiClientException
from serializers.nalog_api_serializer import NalogApiRequestSerializer
from settings import Settings


class NalogApiClient:
    CLIENT_EXCEPTIONS = (
        NalogApiClientException,
        aiohttp.ClientProxyConnectionError,
        aiohttp.ServerTimeoutError,
    )

    def __init__(self, settings: Settings, logger: AppLogger) -> None:
        self.nalog_api_service_url = settings.client_nalog_url
        self.request_timeout = settings.client_nalog_timeout_sec
        self.retries_times = settings.client_nalog_retries
        self.retries_wait = settings.client_nalog_wait_sec
        self.logger = logger
        self.timeout = aiohttp.ClientTimeout(total=self.request_timeout)

    @property
    def _headers(self):
        return {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ru-RU,ru",
            "Connection": "keep-alive",
            "Origin": "https://service.nalog.ru",
            "Referer": "https://service.nalog.ru/inn.do",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "X-Requested-With": "XMLHttpRequest",
        }

    async def send_request_for_inn(self, nalog_api_request: NalogApiRequestSerializer) -> Optional[str]:
        """
        Отправка запроса в API service.nalog.ru
        """
        self.logger.debug(f'Request to nalog api service for {nalog_api_request.client_fullname}')

        form_data = nalog_api_request.dict(by_alias=True)

        @retry(self.CLIENT_EXCEPTIONS, logger=self.logger, attempts=self.retries_times, wait_sec=self.retries_wait)
        async def make_request(client_session: aiohttp.ClientSession):
            async with client_session.post(url=self.nalog_api_service_url, data=form_data) as response:
                if response.status not in [http.HTTPStatus.OK, http.HTTPStatus.NOT_FOUND]:
                    response_text = await response.text()
                    raise NalogApiClientException(response_text)
                data = await response.json()
                code = data.get('code')
                captcha_required = data.get('captchaRequired')
                if captcha_required:
                    raise NalogApiClientException(f'Captcha required for request {nalog_api_request.client_fullname}')
                if code == 0:
                    return 'no inn'
                elif code == 1:
                    return data.get('inn')
                else:
                    raise NalogApiClientException(f'Unable to parse response! Details: {response}')

        async with aiohttp.ClientSession(timeout=self.timeout, headers=self._headers) as session:
            return await make_request(session)
