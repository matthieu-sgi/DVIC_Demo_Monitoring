'''Python module to open a connection to a Elasticsearch database'''

from elasticsearch import Elasticsearch


class Database:

    def __init__(self, host: str, port: int, index: str):
        self.host = host
        self.port = port
        self.index = index
        self.es = Elasticsearch([{'host': self.host, 'port': self.port}])
