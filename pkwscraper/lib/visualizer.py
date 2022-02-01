
"""
Concepts dictionary explained:
- unit / territorial unit - single voivodship, constituency, district or
    commune (or whole country);
- values - values assigned to each territorial unit as data to plot;
    this is an input to colormap;
- contours - some units of other granularity that will be
    plotted as contours on top of map;
- colormap - a mapping from numerical values (or vectors) to colors;
- normalizing - converting values for all units to fit into given range;
    default is (0,1);
- color legend - showing colorbar or color square with description of
    edge colors;
- rendered plot - rendered image that is a result of class job, including
    all graphical and text elements;
- map - a part of plot including territorial units, excluding frame,
    legends, title and descriptions.


- granularity (not here... TODO - move to explanation of main
    script/function/class)
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from pkwscraper.lib.region import Region


class Colormap:
    def __init__(self, color_data, interpolation="linear",
                 legend=False, color_descriptions=None,
                 numerical_values=True):
        """
        color_data: ...
        interpolation: 'linear' or 'logarithmic' - method of
            interpolation of values on colormap
        legend: bool - whether to put explanation of extreme colors
            or not (in form of colorbar or color square or sth)
        color_descriptions: ...
        numerical_values: bool - whether to put the percentage values
            corresponding to extreme colors on plot or not
        """
        pass

    def _1d_interpolate(self):
        """ Interpolate color on 1-dimensional segment. """
        pass

    def _nd_interpolate(self):
        """
        Interpolate color in N-dimensional space using triangular mesh.
        """
        pass

    def __call__(self, value):
        """
        Map scalar or vector value on color.

        value: int/float/list/tuple - values to convert
        return: tuple of 3/4 floats in range [0-1] - RGB or RGBA
        """
        pass

    def make_legend(self, ax):
        """ Add color legend to provided axes. """
        pass


class Visualizer:
    def __init__(
        self, regions, values, colormap, contours=None,
        interpolation="linear", normalization_range=(0, 1),
        title=None, color_legend=False, grid=False
    ):
        """
        regions: list of Regions - list of regions to color
        values: list of float - list of values corresponding to regions
        colormap: Colormap or callable - a mapping turning numerical
            values to colors
        contours: list of Regions - contours to put on final map
            without any values or filling
        interpolation: 'linear' or 'logarithmic' - method of
            interpolation of values on colormap
        normalization_range: pair of numbers - range that values for
            different regions will be normalized to, before passing to
            the colormap
        title: str - writing that will be put on top of plot
        color_legend: bool - whether to put explanation of extreme
            colors or not (in form of colorbar or color square or sth)
        grid: bool - whether to plot or not a square frame around map
        """
        # check number of regions and values
        if len(regions) != len(values):
            raise ValueError(
                "`regions` and `values` must be of same length.")

        # check dimensions
        values_shape = np.shape(values)
        range_shape = np.shape(normalization_range)

        if np.ndim(values) == 2:
            # values dimensions (vector length)
            self._vdim = values_shape[1]
        else:
            # scalar values
            self._vdim = None

        if not range_shape[-1] == 2:
            raise ValueError("Range should be pair of min and max values.")

        if np.ndim(normalization_range) == 2:
            # check matching dimension
            if range_shape[0] != values_shape[1]:
                raise ValueError("Pass single range or list of ranges for"
                                 " each dimension of value vectors.")
            # check if ranges satisfy `min < max` condition
            range_array = np.array(normalization_range)
            if not all(range_array[:, 0] < range_array[:, 1]):
                raise ValueError("Second value of range must"
                                 " be greater than first value.")
        else:
            # check `min < max`
            if not normalization_range[0] < normalization_range[1]:
                raise ValueError("Second value of `normalization_range` must"
                                 " be greater than first value.")
            # expand normalization range to match values dimension
            if self._vdim:
                normalization_range = tuple(normalization_range
                                            for i in range(self._vdim))

        # assign values
        self.regions = regions
        self.values = values
        self.colormap = colormap
        self.contours = contours
        self.interpolation = interpolation
        self.normalization_range = normalization_range
        self.title = title
        self.color_legend = color_legend
        self.grid = grid

        # remember mins and maxs of values
        ###############################################
        ###############################################
        ############### TODO - USE TO PLOTING LEGEND AND COLOR KEY
        ###############################################
        ###############################################
        self.maxs = None
        self.mins = None

    def scale(self):
        ################################
        ################################
        ####### TODO - DEPRECATED
        ################################
        ################################
        """
        # DEPRECATED
        Scale geometric data to fit into given coordinates.
        """
        raise NotImplementedError("rejected")

    def normalize_values(self):
        """ Scale values of all individual units to fit desired range. """
        # prepare data
        values = np.array(self.values, dtype=float)
        mins = np.amin(values, axis=0)
        maxs = np.amax(values, axis=0)

        # normalize
        if self._vdim is None:
            # one-dimensional (scalar) values
            new_min, new_max = self.normalization_range

            if maxs > mins:
                values = (values - mins) / (maxs - mins)
                values = values * (new_max - new_min) + new_min
            else:
                values = values * 0 + (new_min + new_max) / 2

        else:
            # multi-dimensional (vector) values
            for i in range(self._vdim):
                values_i = values[:, i]
                mini = mins[i]
                maxi = maxs[i]
                new_mini, new_maxi = self.normalization_range[i]

                if maxi > mini:
                    values_i = (values_i - mini) / (maxi - mini)
                    values_i = values_i * (new_maxi - new_mini) + new_mini
                else:
                    values_i = values_i * 0 + (new_mini + new_maxi) / 2

                values[:, i] = values_i

        # keep results
        self.values = values.tolist()
        self.mins = mins.tolist()
        self.maxs = maxs.tolist()

    def render_colors(self):
        """ Convert values to colors using colormap. """
        self.colors = [self.colormap(value) for value in self.values]

    def prepare(self):
        """ Put all data and format the plot, before rendering. """
        # get ranges
        ranges = [region.get_xy_range() for region in self.regions
                  if not region.is_empty()]
        x_min = min(r["x_min"] for r in ranges)
        x_max = max(r["x_max"] for r in ranges)
        y_min = min(r["y_min"] for r in ranges)
        y_max = max(r["y_max"] for r in ranges)

        # get patch collection of units
        kwargs_list = [{"color": color} for color in self.colors]
        path_collection = Region.to_mpl_collection(
            regions=self.regions, kwargs_list=kwargs_list, antialiased=True)

        # get patch collection of bigger units contours
        if self.contours:
            contours_kwargs = len(self.contours) * [
                {"facecolor": None, "fill": False, "edgecolor": "k"}]
            contours_collection = Region.to_mpl_collection(
                regions=self.contours, kwargs_list=contours_kwargs,
                antialiased=True)

        # make plot
        fig, ax = plt.subplots()
        ax.axis('equal')
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.invert_yaxis()

        # put patches on axes
        ax.add_collection(path_collection)
        if self.contours:
            ax.add_collection(contours_collection)

    def save_image(self, filepath):
        """ Render plot to file. """
        plt.savefig(filepath)
        plt.close()

    def show(self):
        """ Render plot to window. """
        plt.show()
        plt.close()
