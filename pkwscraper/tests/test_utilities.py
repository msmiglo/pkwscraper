
from decimal import Decimal
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

from pkwscraper.lib.utilities import get_parent_code, Region


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


# TODO: move it to lib classes tests maybe
class TestRegion(TestCase):
    """
    - test round decimal
    - test get line start
    - test init
    - test load from empty svg
    - test load from svg
    - test save to json
    - test load from json
    - test filling_boundaries_line
    - test contour_lines
    - test is empty
    - test xy range
    """
    def setUp(self):
        region_data = [[
            [
                ['9.2', '3.0'], ['11.2', '3.0'], ['13.2', '5.0'],
                 ['13.2', '7.0'], ['11.2', '9.0'], ['9.2', '9.0'],
                 ['7.2', '7.0'], ['7.2', '5.0']
            ],
            [
                ['12.0', '5.4'], ['13.0', '5.4'], ['14.0', '6.4'],
                ['14.0', '7.4'], ['13.0', '8.4'], ['12.0', '8.4'],
                ['11.0', '7.4'], ['11.0', '6.4']
            ],
            [
                ['11.0', '7.0'], ['10.0', '8.0'], ['10.0', '9.0'],
                ['11.0', '10.0'], ['13.0', '9.0'], ['13.0', '8.0'],
                ['12.0', '7.0']
            ],
            [
                ['10.0', '6.0'], ['9.0', '7.0'], ['9.0', '8.0'],
                ['10.0', '9.0'], ['12.0', '8.0'], ['12.0', '7.0'],
                ['11.0', '6.0']
            ]
        ]]
        self.region_data = [[[[Decimal(str(coord))
                               for coord in point]
                              for point in curve]
                             for curve in shape]
                            for shape in region_data]
        self.empty_region_data = [[]]
        self.json_txt = ("[[[[9.2,3.0],[11.2,3.0],[13.2,5.0],[13.2,7.0],"
            "[11.2,9.0],[9.2,9.0],[7.2,7.0],[7.2,5.0]],[[12.0,5.4],"
            "[13.0,5.4],[14.0,6.4],[14.0,7.4],[13.0,8.4],[12.0,8.4],"
            "[11.0,7.4],[11.0,6.4]],[[11.0,7.0],[10.0,8.0],[10.0,9.0],"
            "[11.0,10.0],[13.0,9.0],[13.0,8.0],[12.0,7.0]],[[10.0,6.0],"
            "[9.0,7.0],[9.0,8.0],[10.0,9.0],[12.0,8.0],[12.0,7.0],[11.0,6.0]]]]")
        self.geo_txt = (
            "    M9.2,3l2,0l2,2l0,2l-2,2l-2,0l-2-2l0-2l2-2L9.2,3"
            "    M12,5.4l1,0l1,1l0,1l-1,1l-1,0l-1-1l0-1l1-1L12,5.4"
            "    M11,7l-1,1l0,1l1,1l2-1l0-1l-1-1l-1,0L11,7"
            "    M10,6l-1,1l0,1l1,1l2-1l0-1l-1-1l-1,0L10,6    "
        )
        x_min = Decimal("7.2")
        x_max = 14
        y_min = 3
        y_max = 10
        self.xy_range = {
            "x": (x_min, x_max), "y": (y_min, y_max),
            "min": (x_min, y_min), "max": (x_max, y_max),
            "x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max
        }

    def tearDown(self):
        pass

    def test_round_decimal(self):
        # arrange
        mock_a = MagicMock()
        mock_b = MagicMock()
        _MockDecimalClass = MagicMock()
        _MockDecimalClass.side_effect = [mock_a, mock_b]
        # act
        with self.assertRaises(TypeError):
            Region._round_decimal("5.2")
        with patch("pkwscraper.lib.utilities.Decimal", _MockDecimalClass):
            decimal_a = Region._round_decimal(1.2357, precision=2)
            decimal_b = Region._round_decimal(-4.19999999999999999)
        # assert
        self.assertEqual(_MockDecimalClass.call_count, 2)
        _MockDecimalClass.assert_has_calls([call('1.24'), call('-4.2')])
        self.assertIs(decimal_a, mock_a)
        self.assertIs(decimal_b, mock_b)

    def test_get_line_start(self):
        # arrange
        mock_element = MagicMock()
        mock_element.start = 5.0 + 1.237j
        mock_element.end = -2.24 + 0.1j
        mock_x = MagicMock()
        mock_y = MagicMock()
        mock_region_round = MagicMock()
        mock_region_round.side_effect = [mock_x, mock_y]
        # act
        with patch("pkwscraper.lib.utilities.Region._round_decimal",
                   mock_region_round):
            result = Region._get_line_start(mock_element)
        # assert
        self.assertEqual(mock_region_round.call_count, 2)
        mock_region_round.assert_has_calls([call(5.), call(1.237)])
        self.assertIsInstance(result, list)
        self.assertListEqual(result, [mock_x, mock_y])

    def test_init(self):
        region = Region(self.region_data)
        self.assertListEqual(region.data, self.region_data)

    def test_load_from_empty_svg(self):
        with self.assertRaises(TypeError):
            reg_1 = Region.from_svg_d(None)
        reg_2 = Region.from_svg_d("   ")
        self.assertListEqual(reg_2.data, [[]])
        reg_3 = Region.from_svg_d("")
        self.assertListEqual(reg_3.data, [[]])

    def test_load_from_svg(self):
        reg = Region.from_svg_d(self.geo_txt)
        self.assertEqual(len(reg.data), len(self.region_data))
        for shape_a, shape_b in zip(reg.data, self.region_data):
            self.assertEqual(len(shape_a), len(shape_b))
            for curve_a, curve_b in zip(shape_a, shape_b):
                self.assertEqual(len(curve_a), len(curve_b))
                for point_a, point_b in zip(curve_a, curve_b):
                    self.assertEqual(len(point_a), len(point_b))
                    for coord_a, coord_b in zip(point_a, point_b):
                        self.assertEqual(len(shape_a), len(shape_b))
                        self.assertEqual(coord_a, coord_b)

    def test_save_to_json(self):
        region = Region(self.region_data)
        json_txt = region.json()
        self.assertEqual(json_txt, self.json_txt)

    def test_load_from_json(self):
        region = Region.from_json(self.json_txt)
        self.assertEqual(region.data, self.region_data)

    def test_filling_boundaries_line(self):
        region = Region(self.region_data)
        line = region.filling_boundaries_line
        self.assertEqual(len(line), 34)

    def test_contour_lines(self):
        region = Region(self.region_data)
        lines = region.contour_lines
        self.assertEqual(len(lines), 4)

    def test_is_empty(self):
        region_1 = Region(self.region_data)
        self.assertFalse(region_1.is_empty())
        region_2 = Region(self.empty_region_data)
        self.assertTrue(region_2.is_empty())

    def test_xy_range(self):
        region = Region(self.region_data)
        xy_range = region.get_xy_range()
        self.assertDictEqual(xy_range, self.xy_range)


if __name__ == "__main__":
    main()
