from typing import Optional
from datetime import datetime

from core.exceptions import NalogApiClientException
from settings import Settings
from logger import AppLogger

from serializers.request_serializer import RequestMqSerializer
from serializers.nalog_api_serializer import NalogApiRequestSerializer
from clients.inn_nalog_client import NalogApiClient
from models.model import ClientDataModel, ClientDataDTO
from repositories.request_mongo_repository import RequestRepository


class InnService:
    def __init__(
            self,
            settings: Settings,
            logger: AppLogger,
            client: NalogApiClient,
            storage: RequestRepository
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.client = client
        self.storage_repository = storage

    async def get_client_inn_from_storage(self, client_data: RequestMqSerializer) -> Optional[ClientDataModel]:
        client_passport = f'{client_data.document_serial} {client_data.document_number}'
        client_request = await self.storage_repository.find_client_data(client_passport, client_data.request_id)
        return client_request

    def update_status(self, model: ClientDataModel, inn: str, error: str) -> None:
        model.inn = inn
        model.error = error

    async def get_client_inn(self, client_data: RequestMqSerializer) -> ClientDataDTO:
        """Получение клиентского ИНН"""
        start_process = datetime.utcnow()
        model = ClientDataModel.create_from_request(client_data)

        # Получить данные из БД
        existing_data = await self.get_client_inn_from_storage(client_data)
        if existing_data:
            elapsed_time = (datetime.utcnow() - start_process).total_seconds()
            return ClientDataDTO(
                request_id=client_data.request_id,
                inn=existing_data.inn,
                elapsed_time=elapsed_time,
                cashed=True
            )

        # Сделать фактический запрос в Nalog API
        request = NalogApiRequestSerializer.create_from_request(client_data)
        error, result = None, ''
        try:
            result = await self.client.send_request_for_inn(request)
        except NalogApiClientException as exception:
            self.logger.error('Error request to Nalog api service', details=str(exception))
            error = str(exception)

        self.update_status(model, result, error)
        await self.storage_repository.save_client_data(model)

        return ClientDataDTO(
            request_id=model.request_id,
            inn=model.inn,
            details=model.error,
            elapsed_time=model.elapsed_time
        )
