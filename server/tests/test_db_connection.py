'''Module for testing database connection'''

import unittest

from server.database.elk_stack.database_modules.database_driver import Database

class TestDatabaseConnection(unittest.TestCase):
    def setUp(self):
        self.db = Database('localhost', 9200, 'test_index')
    
    def test_connection(self):
        print('Testing connection to database...')
        self.assertTrue(self.db.test_connection())
    

if __name__ == '__main__':
    unittest.main()