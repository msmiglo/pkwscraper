
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

from pkwscraper.lib.utilities import get_parent_code


class TestGetParentCode(TestCase):
    """
    - test empty input
    - test wrong format
    - test over voivodships range
    - test odd voivodship number
    - test voivodship parent
    - test too long number
    - test too short number
    - test integer codes
    - test string codes
    """
    def setUp(self):
        self.data = (
            (20100, 20000),
            ("020100", "20000"),
            ("020105", "20100"),
            ("086400", "80000"),
            (146501, 146500),
            (149901, 149900),
            (149900, 140000),
            (146515, 146500),
            (146503, 146500),
            (146500, 140000),
            (326100, 320000),
            (120101, 120100),
            (126512, 126500),
            (123456, 123400),
            (26215, 26200),
            (40200, 40000),
        )

    def tearDown(self):
        pass

    def test_empty_input(self):
        input_code = ""
        with self.assertRaises(ValueError):
            get_parent_code(input_code)

    def test_wrong_format(self):
        input_code = b"080312"
        with self.assertRaises(TypeError):
            get_parent_code(input_code)

    def test_over_voivodships_range(self):
        input_code = 346102
        with self.assertRaises(ValueError):
            get_parent_code(input_code)

    def test_odd_voivodship_number(self):
        input_code = 130612
        with self.assertRaises(ValueError):
            get_parent_code(input_code)

    def test_voivodship_parent(self):
        input_code = 280000
        with self.assertRaises(ValueError):
            get_parent_code(input_code)

    def test_too_long_number(self):
        input_code = 2205142
        with self.assertRaises(ValueError):
            get_parent_code(input_code)

    def test_too_short_number(self):
        input_code = 2058
        with self.assertRaises(ValueError):
            get_parent_code(input_code)

    def test_integer_codes(self):
        for input_code, expected in self.data:
            input_code = int(input_code)
            expected = int(expected)
            result = get_parent_code(input_code)
            self.assertEqual(result, expected)
            self.assertIs(type(result), type(expected))

    def test_string_codes(self):
        for input_code, expected in self.data:
            input_code = str(input_code)
            expected = str(expected)
            result = get_parent_code(input_code)
            self.assertEqual(result, expected)
            self.assertIs(type(result), type(expected))


if __name__ == "__main__":
    main()
