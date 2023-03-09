'''Driver for database connections'''

from abc import ABC, abstractmethod
from elasticsearch import Elasticsearch

# In development
class DatabaseConnector(ABC):
    def __init__(self, host: str, port: int, index: str = None):
        self.host = host
        self.port = port
        self.index = index    




class ElasticConnector:
    '''Driver for ElasticSearch database
    
    Args:
        host (str): Host of the database
        port (int): Port of the database
        index (str): Index of the database
    '''

    def __init__(self, host: str, port: int, index: str):
        self.host = host
        self.port = port
        self.index = index
        self.es = Elasticsearch(f'http://{self.host}:{self.port}')
        if self.index is not None:
            self._create_index(self.index)
    
    def test_connection(self) -> bool:
        return self.es.ping()
    
    def _create_index(self, index = None) -> None:
        '''Creates index if it does not exist'''
        self.index = index
        if not self.es.indices.exists(index=self.index):
            self.es.indices.create(index=self.index)
    
    def insert(self, data: dict) -> str:
        '''Inserts data into database and returns the id of the inserted data'''
        return str(self.es.index(index=self.index, document=data))

    def get_by_id(self, id: str) -> dict:
        '''Returns data from database by id'''
        return self.es.get(index=self.index, id=id)

    def search(self, query: dict) -> dict:
        '''Returns data from database by query'''
        return self.es.search(index=self.index, query=query)
    
    def delete_by_id(self, id: str) -> None:
        '''Deletes data from database by id'''
        self.es.delete(index=self.index, id=id)
    
    def update(self, id: str, data: dict) -> None:
        '''Updates data in database by id'''
        self.es.update(index=self.index, id=id, body=data)
    
    def delete_index(self) -> None:
        '''Deletes index from database'''
        self.es.indices.delete(index=self.index)
    
    def get_all(self) -> dict:
        '''Returns all data from database'''
        return self.es.search(index=self.index, size=100, query={'match_all': {}})
    
    def delete_all(self) -> None:
        '''Deletes all data from database'''
        self.es.delete_by_query(index=self.index, query={'match_all': {}})
    
    def get_index_name(self) -> str:
        '''Returns the name of the index'''
        return self.index
    
    def push_log(self, log: dict) -> None:
        '''Pushes log to database'''
        self.insert(log)

    
if __name__ == '__main__':
    db = ElasticConnector('localhost', 9200, 'test_index')
    print(db.test_connection())
    # print(db.delete_all())
    # print(db.insert({'name': 'test'}))
    print(db.get_all())
    # db.delete_all()
    # print("------------------")
    # print(db.get_all())
    # print("------------------")
    # db.insert({'name': 'test'})
    # print(db.get_all())
