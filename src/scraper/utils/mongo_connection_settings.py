import os
from dataclasses import dataclass
from .cryptography_helper import CryptographyHelper


@dataclass()
class MongoConnectionSettings:
    CONNECTION_STRING_TEMPLATE = 'mongodb+srv://<user>:<password>@<host>/admin?retryWrites=true&w=majority'

    def __init__(self):
        self.host = os.getenv('MONGO_HOST')
        self.username = os.getenv('MONGO_USER')
        self.password = CryptographyHelper.decrypt(os.getenv('MONGO_PASS'))
        self.database = os.getenv('MONGO_DATABASE')
        self.collections = os.getenv('MONGO_COLLECTIONS')
