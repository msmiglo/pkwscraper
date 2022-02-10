
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

from pkwscraper.lib.controller import Controller, DbReferences


class TestDbReferences(TestCase):
    """
    - test inverse dict
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_inverse_dict(self):
        # arrange
        dictionary_1 = {}
        dictionary_2 = {
            "Moscow": ["Russia"],
            "Sankt Petersburg": ["Russia"],
            "Washington": ["USA"],
            "Chicago": ["USA"],
            "New Jersey": ["USA"],
        }
        dictionary_3 = {
            "Numbers": [1, 2, 3, 8, "O"], "Letters": ["a", "x", "O"],}
        expected_1 = {}
        expected_2 = {
            "Russia": ["Moscow", "Sankt Petersburg"],
            "USA": ["Washington", "Chicago", "New Jersey"],
        }
        expected_3 = {
            1: ["Numbers"], 2: ["Numbers"], 3: ["Numbers"], 8: ["Numbers"],
            "a": ["Letters"], "x": ["Letters"],
            "O": ["Numbers", "Letters"]
        }
        # act
        result_1 = DbReferences.inverse_dict(dictionary_1)
        result_2 = DbReferences.inverse_dict(dictionary_2)
        result_3 = DbReferences.inverse_dict(dictionary_3)
        # assert
        self.assertDictEqual(result_1, expected_1)
        self.assertDictEqual(result_2, expected_2)
        self.assertDictEqual(result_3, expected_3)
        # NOTE: this tests assumes dict insertion order preserved, so it
        # is intended to be run on Python 3.7+


class TestController(TestCase):
    """
    - test 
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_(self):
        # arrange
        
        # act
        
        # assert
        
        pass


if __name__ == "__main__":
    main()
