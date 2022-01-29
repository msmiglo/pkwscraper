
from decimal import Decimal
import json

from matplotlib.collections import PatchCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import svg.path
from svg.path import parse_path

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

    def to_json(self):
        """ Serialize to JSON. """
        data = [[[[float(coord)
                   for coord in point]
                  for point in curve]
                 for curve in shape]
                for shape in self.data]

        return json.dumps(data, separators=(',', ':'))

    def to_mpl_path(self, **kwargs):
        """
        Make an `PathPatch` object that can be added to matplotlib
        plot.

        `kwargs` are passed to PathPatch constructor.
        """
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
        return patch

    @staticmethod
    def to_mpl_collection(regions, kwargs_list, **collection_kwargs):
        """
        Create `PatchCollection` object that can be added to
        matplotlib plot and rendered. It takes `Region` objects
        and list of keyword arguments to be passed to creation
        of each PathPatch.

        `regions` - list of Region
        `kwargs_list` - a list of kwargs that will be passed to
            method `to_mpl_path` called for each Region from
            `regions` list. Both lists must be of the same length.
        `collection_kwargs` - kwargs passed to the constructor of
            `PatchCollection` object along with list of patches.

        NOTE: empty regions are omitted from creating patches.
        """
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
        """
        Check if Region is empty (has no geometric entities defined).
        """
        if len(self.data) == 1 and len(self.data[0]) == 0:
            return True
        else:
            return False

    def get_xy_range(self):
        """
        Get the data of maximum and minimum span of x- and
        y-coordinates. It returns dictionary with different
        arrangements of x_min, x_max, y_min and y_max for
        convenience.
        """
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
