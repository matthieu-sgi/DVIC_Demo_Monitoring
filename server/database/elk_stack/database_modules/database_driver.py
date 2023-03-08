'''Driver for database connections'''

from elasticsearch import Elasticsearch


class Database:

    def __init__(self, host: str, port: int, index: str = None):
        self.host = host
        self.port = port
        self.index = index
        self.es = Elasticsearch(f'http://{self.host}:{self.port}')
        if self.index is not None:
            self.create_index(self.index)
    
    def test_connection(self) -> bool:
        return self.es.ping()
    
    def create_index(self, index = None) -> None:
        self.index = index
        if not self.es.indices.exists(index=self.index):
            self.es.indices.create(index=self.index)
    
    def insert(self, data: dict) -> None:
        self.es.index(index=self.index, document=data)

    def get_by_id(self, id: str) -> dict:
        return self.es.get(index=self.index, id=id)

    def search(self, query: dict) -> dict:
        return self.es.search(index=self.index, query=query)
    
    def delete_by_id(self, id: str) -> None:
        self.es.delete(index=self.index, id=id)
    
    def update(self, id: str, data: dict) -> None:
        self.es.update(index=self.index, id=id, body=data)
    
    def delete_index(self) -> None:
        self.es.indices.delete(index=self.index)
    
    def get_all(self) -> dict:
        return self.es.search(index=self.index, size=100, query={'match_all': {}})
    
    def delete_all(self) -> None:
        self.es.delete_by_query(index=self.index, query={'match_all': {}})
    
    def get_index_name(self) -> str:
        return self.index

    
if __name__ == '__main__':
    db = Database('localhost', 9200, 'test_index')
    print(db.test_connection())
    print(db.delete_all())
    print("------------------")
    print(db.get_all())
    print("------------------")
    db.insert({'name': 'test'})
    print(db.get_all())
