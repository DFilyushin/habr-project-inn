from pydantic import BaseModel, Field

from serializers.request_serializer import RequestMqSerializer


class NalogApiRequestSerializer(BaseModel):
    last_name: str = Field(None, alias='fam')
    first_name: str = Field(None, alias='nam')
    middle_name: str = Field('нет', alias='otch')
    birth_date: str = Field(None, alias='bdate')
    birth_place: str = Field('', alias='bplace')
    doc_type: int = Field(21, alias='doctype')
    doc_number: str = Field(None, alias='docno')
    doc_date: str = Field(None, alias='docdt')
    type: str = Field('innMy', alias='c')
    captcha: str = Field('', alias='captcha')
    captchaToken: str = Field('', alias='captchaToken')

    @property
    def client_fullname(self):
        return f'{self.last_name} {self.first_name} {self.middle_name}'

    @classmethod
    def create_from_request(cls, request: RequestMqSerializer) -> 'NalogApiRequestSerializer':
        document_number = '{} {} {}'.format(
            request.document_serial[0:2],
            request.document_serial[2:4],
            request.document_number
        )
        return NalogApiRequestSerializer(
            last_name=request.last_name,
            first_name=request.first_name,
            middle_name=request.middle_name,
            birth_date=request.birth_date.strftime('%d.%m.%Y'),
            doc_number=document_number,
            doc_date=request.document_date.strftime('%d.%m.%Y')
        )

    class Config:
        allow_population_by_field_name = True
