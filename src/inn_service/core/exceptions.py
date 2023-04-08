class MongoConnectionError(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f'Mongo connection problem: {self.message}'


class NalogApiClientException(Exception):
    pass
