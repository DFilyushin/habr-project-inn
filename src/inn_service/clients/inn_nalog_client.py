import http
import random
from logger import AppLogger
from typing import Optional

import aiohttp

from clients.utils import retry
from core.exceptions import NalogApiClientException
from serializers.nalog_api_serializer import NalogApiRequestSerializer
from settings import Settings

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Linux; U; Android 11; es-SA; TECNO KG5k Build/RP1A.201005.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.81 Mobile Safari/537.36 PHX/10.7",
    "Mozilla/5.0 (Linux; Android 12; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.118 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; U; Android 11; es-MX; Redmi Note 8T Build/RKQ1.201004.002) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.75 Mobile Safari/537.36 XiaoMi/MiuiBrowser/13.16.1-gn",
    "Mozilla/5.0 (Linux; Android 12; SAMSUNG SM-T220) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/18.0 Chrome/99.0.4844.74 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-T290) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.56 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; C6L 2021) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.126 Mobile Safari/537.36"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 OPR/76.0.4017.123",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.57",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36 Edg/90.0.818.66",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; M2102J20SG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.34 Mobile Safari/537.36"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.5304.105 Safari/537.36 OpenWave/92.4.9903.4"
    "Mozilla/5.0 (Windows NT 10.0; rv:99.0) Gecko/20100101 Firefox/99.0"
    "Mozilla/5.0 (Linux; Android 9; moto e6 (XT2005DL)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.69 Mobile Safari/537.36"
    "Mozilla/5.0 (Linux; Android 10; SM-A013M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.81 Mobile Safari/537.36"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.0 Safari/537.36"
    "Mozilla/5.0 (Linux; Android 10; AGR-W09) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
]


class NalogApiClient:
    CLIENT_EXCEPTIONS = (
        NalogApiClientException,
        aiohttp.ClientProxyConnectionError,
        aiohttp.ServerTimeoutError,
    )

    def __init__(self, settings: Settings, logger: AppLogger):
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
            "User-Agent": random.choice(USER_AGENTS),
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
