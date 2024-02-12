import unittest
import os
import csv
from tools import append_to_csv

class TestAppendToCSVWithID(unittest.TestCase):
    def setUp(self):
        self.test_file = 'test_file.csv'

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    async def test_append_to_csv_with_id(self):
        row_data = ['test1', 'test2', 'test3']
        status = await append_to_csv(self.test_file, row_data)

        with open(self.test_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for i, row in enumerate(reader):
                self.assertEqual(i+1, int(row[0]))
                self.assertEqual(row_data, row[1:])

if __name__ == '__main__':
    unittest.main()