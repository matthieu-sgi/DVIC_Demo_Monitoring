'''Module for testing database connection'''

import unittest

from server.dvic_log_server.database_drivers import ElasticConnector

class TestDatabaseConnection(unittest.TestCase):
    def setUp(self):
        self.db = ElasticConnector('localhost', 9200, 'test_index')
    
    def test_connection(self):
        print('Testing connection to database...')
        self.assertTrue(self.db.test_connection())
    

if __name__ == '__main__':
    unittest.main()