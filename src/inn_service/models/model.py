from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime

from serializers.request_serializer import RequestSerializer


class RequestModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
    first_name: str
    last_name: str
    middle_name: str
    birth_date: datetime
    birth_place: str
    passport_num: str
    document_date: datetime
    executed_at: Optional[datetime]
    inn: Optional[str]
    error: Optional[str]

    @classmethod
    def create_from_request(cls, request: RequestSerializer) -> 'RequestModel':
        return RequestModel(
            request_id=request.request_id,
            first_name=request.first_name,
            last_name=request.last_name,
            middle_name=request.middle_name,
            birth_date=datetime.combine(request.birth_date, datetime.min.time()),
            birth_place=request.birth_place,
            passport_num='{} {}'.format(request.document_serial, request.document_number),
            document_date=datetime.combine(request.document_date, datetime.min.time()),
        )

    @property
    def elapsed_time(self) -> float:
        end = self.executed_at or datetime.utcnow()
        return (end - self.created_at).total_seconds()

    def set_result(self, inn: str) -> None:
        self.inn = inn
        self.executed_at = datetime.utcnow()


class RequestDTO(BaseModel):
    request_id: str
    inn: str
    details: Optional[str]
    cashed: bool = False
    elapsed_time: float
