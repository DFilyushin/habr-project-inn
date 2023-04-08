from datetime import date
from pydantic import BaseModel, Field


class RequestSerializer(BaseModel):
    request_id: str = Field(alias='requestId')
    first_name: str = Field(alias='firstName')
    last_name: str = Field(alias='lastName')
    middle_name: str = Field(alias='middleName')
    birth_date: date = Field(alias='birthDate')
    birth_place: str = Field(alias='birthPlace')
    document_serial: str = Field(alias='documentSerial')
    document_number: str = Field(alias='documentNumber')
    document_date: date = Field(alias='documentDate')
