from pydantic import BaseModel
from datetime import date, datetime


class RequestModel(BaseModel):
    created_at: datetime
    request_id: str
    first_name: str
    last_name: str
    middle_name: str
    birth_date: date
    birth_place: str
    passport_num: str
    document_date: date
