
from decimal import Decimal
import json

import svg.path
from svg.path import parse_path
#from svg.path import Path

"""
EXPLANATION OF TERRITORY CODES:

EN:
- Code for commune has 6 digits:
    * 2 for voivodship,
    * 2 for district,
    * 2 for commune.
- Zero does not count - 00 on the end means this is whole district
      code, and 0000 at the end means this is whole voivodship code.
- Voivodships ("województwo") numbers are even, that is from 2 to 32.
- Leading zero can be omitted for voivodships from 02 to 08.
- Districts ("powiat") have numbers from 01 up.
- Cities with the district status ("powiat grodzki") have numbers from
      61 up, but some may be skipped by one.
- Communes ("gmina") have numbers from 01 up every 1.
- Among cities with the district status, only Warsaw has city-districts
      ("dzielnica") as communes, but the number 01 is reserved so they
      have number from 02 to 19.
- Warsaw as a district has code 14 65 01, so it is strange, because it
      should have 14 65 00.
- 14 99 00 is a code for abroad as the district and it has one commune
    level unit with code 14 99 01. The "abroad district" is part of the
    MAZOWIECKIE voivodship (code 140000) and constituency no 19.


PL (WYTŁUMACZENIE KODÓW TERYTORIALNYCH):
- Numer gminy to 6 cyfr:
    * 2 na województwo,
    * 2 na powiat,
    * 2 na gminę.
- Zero się nie liczy - gdy na końcu jest 00 to znaczy, że jest to kod
      całego powiatu, jeśli na końcu jest 0000 to jest to kod całego
      województwa.
- Województwo ma numery parzyste, czyli od 2 do 32.
- Zero z przodu może być pominięte dla województw od 02 do 08.
- Powiaty mają numer od 01 w górę.
- Powiaty grodzkie mają numery od 61 w górę, ale może przeskoczyć o jedno.
- Gminy mają numery od 01 w górę co 1.
- Z powiatów grodzkich tylko Warszawa ma dzielnice jako gminy,
      ale są numerowane bez numerka 01, czyli jest od 02 do 19.
- Warszawa jako powiat ma kod 14 65 01, więc w ogóle dziwnie,
      bo powinna mieć 14 65 00.
- 14 99 00 to kod dla zagranicy jako powiatu i ma on tylko jedną jednostkę
      na poziomie gminy o kodzie 14 99 01. "Powiat" zagraniczny jest
      częścią województwa Mazowieckiego (o kodzie 140000) i okręgu nr 19.

UPDATE NOTE: this is not common for all elections.
TODO: move the definition of this function to preprocessing step and make
copy for each elections or change codes in data in preprocessing step.
"""

def get_parent_code(code):
    if isinstance(code, str):
        return _get_parent_code_str(code)
    elif isinstance(code, int):
        return _get_parent_code_int(code)
    else:
        raise TypeError(f"Expected type `int` or `str`, got: {type(code)}.")


def _get_parent_code_int(code_int):
    voivod_code = code_int // 10000
    if voivod_code % 2 == 1 or not (0 < voivod_code <= 32):
        raise ValueError(f'Wrong voivodship prefix value: {code_int}.')
    # TODO - VERIFY THE CASE OF WARSAW CODE(S) IN OTHER ELECTIONS
    #if code_int == 149901:
    #    return 146501
    #if code_int == 146501:
    #    return 140000
    #if code_int // 100 == 1465:
    #    return 146501
    if code_int % 10000 == 0:
        raise ValueError("Voivodships do not have parents.")
    if code_int % 100 == 0:
        return 10000 * (code_int // 10000)
    if code_int % 1 == 0:
        return 100 * (code_int // 100)
    raise ValueError(f'Wrong code format: {code_int}.')


def _get_parent_code_str(code_str):
    code_int = int(code_str)
    parent_int = _get_parent_code_int(code_int)
    parent_str = str(parent_int)
    return parent_str


"""
EXPLANATION OF GEO/REGION DATA:

geo - description of region as accepted by "d" attribute in "svg" HTML tag
region - set of shapes that make up the whole region, may contain separate
    shapes
shape - a single compact area, can have holes, it is represented by non
    crossing curves: the first curve defines the outer boundary, and the
    latter ones define boundaries of possible holes in it
curve - set of points that defines the closed polygon contour consisting of
    segments, the last point does not need to be equal to the first one
point - a pair of 2 numbers representing x and y coordinates
number - single coordinate, especially in the geo str where numbers are not
    divided into single-point-pairs

The data is stored in list of lists, 4 levels deep:
region = [shapes]
shape = [curves]
curve = [points]
point = [x, y]
"""

# TODO: move it to separate module in lib classes maybe
class Region:
    def __init__(self, region_data):
        pass

    @staticmethod
    def _get_line_start(line):
        start = line.start
        x, y = start.real, start.imag
        x = Decimal(str(round(x, 8)))
        y = Decimal(str(round(y, 8)))
        return (x, y)

    @classmethod
    def from_svg_d(cls, geo_txt):
        """
        Load from text as in d attribute of svg HTML tag.
        """
        # now:
        # - parse
        path = parse_path(geo_txt)
        # - split curves
        shapes = []
        for elem in path:
            print(elem)
        # - omit repetition of first point
        # - do not check orientation for now
        # - assert end equals start

        # TODO:
        # use decimal to store numbers
        # iterate over curves
        # read orientation of first curve
        # if next curve has opposite orientation - it is a hole
        # if next curve has same orientation as first - it is new shape



        return
        curves = []
        curve = []
        for elem in path:
            if isinstance(elem, svg.path.path.Move):
                curves.append(curve)
                curve = []
            else:
                assert isinstance(elem, svg.path.path.Line)
                curve.append(elem)
        curves.append(curve)
        curves = curves[1:]
        curves = [[_line_to_point(line) for line in curve] for curve in curves]
        return curves

        data = geo
        return cls(data)

    @classmethod
    def from_json(cls, text):
        """
        Load from JSON.
        - text: str/bytes - raw content of json
        """
        data = text
        return cls(data)

    def json(self):
        """ Serialize to JSON. """
        pass

    @property
    def filling_boundaries_line(self):
        """
        Get single line that defines region area with possible holes
        and separate shapes. This contains segments that join shapes
        and holes, so it is NOT suitable to draw contour of region.
        """
        pass

    @property
    def contour_lines(self):
        """
        Get set of lines that defines edge of region with possible holes
        and separate shapes. This does NOT contain segments that join
        separate shapes, so it IS suitable to draw contour of region.
        """
        pass



"""
OLD CODE:



def _line_to_point(line):
    start = line.start
    return (start.real, start.imag)


def geo_to_region(map_str):
    path = parse_path(map_str)
    curves = []
    curve = []
    for elem in path:
        if isinstance(elem, svg.path.path.Move):
            curves.append(curve)
            curve = []
        else:
            assert isinstance(elem, svg.path.path.Line)
            curve.append(elem)
    curves.append(curve)
    curves = curves[1:]
    curves = [[_line_to_point(line) for line in curve] for curve in curves]
    return curves


# --------------- OLD APPROACH ---------------
def _split_part_by_minuses(part_str):
    if "-" not in part_str:
        return [part_str]
    numbers = part_str.split("-")
    numbers = [numbers[0]] + ["-" + num for num in numbers[1:]]
    numbers = list(filter(None, numbers))
    return numbers


def _resolve_points(line_str):
    parts = line_str.split(" ")
    parts = [part.strip() for part in parts]
    numbers = []
    for part_i in parts:
        numbers += _split_part_by_minuses(part_i)
    numbers = [int(num) for num in numbers]
    x_coords = numbers[0::2]
    y_coords = numbers[1::2]
    points = list(zip(x_coords, y_coords))
    return points


def geo_to_region_2(map_str):
    # TODO: finish
    lines = []
    chars = "".join(sorted(set(map_str) - set("0123456789- ")))
    assert chars == "LMZ", chars
    #print()
    #print('----------------------')
    #print(map_str)
    lines = map_str.split("Z")
    lines = list(filter(None, lines))
    # TODO - split by Z, then remove L, split by space,
    #   then by minus, but retrieve it, stack in pairs
    #print()
    #print(lines)
    lines = [line.strip("ML ").replace(" L ", " ") for line in lines]
    #print()
    #print(lines)
    lines = [_resolve_points(line_str) for line_str in lines]
    #print()
    #print(lines)
    #print(list(len(lin) for lin in lines))
    #print()
    return lines
"""
