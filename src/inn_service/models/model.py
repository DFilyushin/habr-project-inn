from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime

from serializers.request_serializer import RequestMqSerializer


class ClientDataModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
    first_name: str
    last_name: str
    middle_name: str
    birth_date: datetime
    birth_place: str = Field(default='')
    passport_num: str
    document_date: datetime
    executed_at: Optional[datetime]
    inn: Optional[str]
    error: Optional[str]

    @classmethod
    def create_from_request(cls, request: RequestMqSerializer) -> 'ClientDataModel':
        return ClientDataModel(
            request_id=request.request_id,
            first_name=request.first_name,
            last_name=request.last_name,
            middle_name=request.middle_name,
            birth_date=datetime.combine(request.birth_date, datetime.min.time()),
            passport_num='{} {}'.format(request.document_serial, request.document_number),
            document_date=datetime.combine(request.document_date, datetime.min.time()),
        )

    @property
    def elapsed_time(self) -> float:
        end = self.executed_at or datetime.utcnow()
        return (end - self.created_at).total_seconds()


class ClientDataDTO(BaseModel):
    request_id: Optional[str] = Field(alias='requestId')
    inn: str = Field(alias='inn')
    details: Optional[str] = Field('', alias='details')
    cashed: bool = Field(False, alias='cached')
    elapsed_time: float = Field(alias='elapsedTime')

    class Config:
        allow_population_by_field_name = True