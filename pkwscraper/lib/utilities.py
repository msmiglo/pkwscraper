
from decimal import Decimal
import json

from matplotlib.collections import PatchCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import svg.path
from svg.path import parse_path

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
        self.data = region_data

    @staticmethod
    def _round_decimal(number, precision=8):
        return Decimal(str(round(number, precision)))

    @staticmethod
    def _get_line_start(line):
        start = line.start
        x, y = start.real, start.imag
        x = Region._round_decimal(x)
        y = Region._round_decimal(y)
        return [x, y]

    @classmethod
    def from_svg_d(cls, geo_txt):
        """
        Load from text as in d attribute of svg HTML tag.
        """
        # parse
        path = parse_path(geo_txt)

        # split curves
        shape = []
        for elem in path:
            if isinstance(elem, svg.path.path.Move):
                # start new curve
                curve = []
                shape.append(curve)
                continue
            else:
                # add point to curve
                assert isinstance(
                    elem, (svg.path.path.Line, svg.path.path.Close)
                ), (elem, type(elem))
                point = Region._get_line_start(elem)
                curve = shape[-1]
                curve.append(point)

        # remove repeating point
        for curve in shape:
            if curve[-1] == curve[0]:
                curve.pop()

        # create data and object
        region_data = [shape]
        region = cls(region_data)
        return region

        # TODO:
        # read orientation of first curve
        # if next curve has opposite orientation - it is a hole
        # if next curve has same orientation as first - it is new shape

    @classmethod
    def from_json(cls, text):
        """
        Load from JSON.
        - text: str/bytes - raw content of json
        """
        data = json.loads(text)
        data = [[[[Region._round_decimal(coord)
                   for coord in point]
                  for point in curve]
                 for curve in shape]
                for shape in data]

        return cls(data)

    def json(self):
        # TODO - RENAME TO `to_json`
        """ Serialize to JSON. """
        data = [[[[float(coord)
                   for coord in point]
                  for point in curve]
                 for curve in shape]
                for shape in self.data]

        return json.dumps(data, separators=(',', ':'))

    def to_mpl_path(self, **kwargs):
        # make path object
        vertices = []
        codes = []
        for line in self.data[0]:
            vertices += list(line) + [line[0]]
            n = len(line)
            codes += [Path.MOVETO] + n * [Path.LINETO]
        path = Path(vertices, codes)
        # make patch
        patch = PathPatch(path, **kwargs)
        patch.set_fill(True)
        return patch

    @staticmethod
    def to_mpl_collection(regions, kwargs_list, **collection_kwargs):
        if len(regions) != len(kwargs_list):
            raise ValueError(
                "`regions` and `kwargs_list` must be of same length.")
        patches = [region.to_mpl_path(**kwargs_i)
                   for region, kwargs_i in zip(regions, kwargs_list)
                   if not region.is_empty()]
        collection = PatchCollection(
            patches, match_original=True, **collection_kwargs)
        return collection

    @property
    def filling_boundaries_line(self):
        """
        Get single line that defines region area with possible holes
        and separate shapes. This contains segments that join shapes
        and holes, so it is NOT suitable to draw contour of region.
        """
        points = []
        for shape in self.data:
            for curve in shape:
                for point in curve:
                    points.append(list(point))
                start_point = curve[0]
                points.append(list(start_point))
        return points

    @property
    def contour_lines(self):
        """
        Get set of lines that defines edge of region with possible holes
        and separate shapes. This does NOT contain segments that join
        separate shapes, so it IS suitable to draw contour of region.
        """
        lines = []
        for shape in self.data:
            for curve in shape:
                new_curve = list(curve) + [curve[0]]
                lines.append(new_curve)
        return lines

    def is_empty(self):
        if len(self.data) == 1 and len(self.data[0]) == 0:
            return True
        else:
            return False

    def get_xy_range(self):
        xs = [point[0] for shape in self.data
              for curve in shape for point in curve]
        ys = [point[1] for shape in self.data
              for curve in shape for point in curve]
        x_min = min(xs)
        x_max = max(xs)
        y_min = min(ys)
        y_max = max(ys)
        return {
            "x": (x_min, x_max), "y": (y_min, y_max),
            "min": (x_min, y_min), "max": (x_max, y_max),
            "x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max
        }
