
"""
Concepts dictionary explained:
- unit / territorial unit - single voivodship, constituency, district or
    commune (or whole country);
- values - values assigned to each territorial unit as data to plot;
    this is an input to colormap;
- background - contours of some units of other granularity that will be
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


class Visualizer:
    def __init__(
        self, regions, values, colormap, background=None,
        interpolation="linear", normalization_range=(0, 1),
        title=None, color_legend=False, grid=False
    ):
        """
        ###############
        ############### TODO: rename background to sth like "grid" or sth
        ###############
        regions: list of Regions - list of regions to color
        values: list of float - list of values corresponding to regions
        colormap: Colormap - a mapping turning numerical values to
            colors
        background: list of Regions - contours to put on final map
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
        # check regions and values count
        if len(regions) != len(values):
            raise ValueError(
                "`regions` and `values` must be of same length.")

        # check dimension of values
        values_shape = np.shape(values)
        try:
            self._values_dimension = values_shape[1]
        except IndexError:
            self._values_dimension = None

        # check normalization range
        range_shape = np.shape(normalization_range)
        if range_shape[-1] != 2:
            raise ValueError("Range should be pair of min and max values.")

        if np.ndim(normalization_range) == 1:
            if not normalization_range[0] < normalization_range[1]:
                raise ValueError("Second value of `normalization_range` must"
                                 " be greater than first value.")
        else:
            for pair in normalization_range:
                if not pair[0] < pair[1]:
                    raise ValueError("Second value of range must"
                                     " be greater than first value.")

        # make normalization range for multidimensional
        if self._values_dimension:
            if np.ndim(normalization_range) == 1:
                normalization_range = tuple(
                    normalization_range for i in range(self._values_dimension))

        # assign values
        self.regions = regions
        self.values = values
        self.colormap = colormap
        self.background = background
        self.interpolation = interpolation
        self.normalization_range = normalization_range
        self.title = title
        self.color_legend = color_legend
        self.grid = grid

    def scale(self):
        """
        # DEPRECATED
        Scale geometric data to fit into given coordinates.
        """
        raise NotImplementedError("rejected")

    def normalize_values(self):
        """ Scale values of all individual units to fit desired range. """
        ###############################################
        ###############################################
        ############### TODO - REFACTOR MAYBE
        ###############################################
        ###############################################
        ############## division by zeros can happen if not values dispersion
        ###############################################
        if self._values_dimension is None:
            # one-dimensional (scalar) values
            min_value = min(self.values)
            max_value = max(self.values)

            target_min, target_max = self.normalization_range

            def _normalize(value):
                v = (value - min_value) / (max_value - min_value)
                target_value = v * (target_max - target_min) + target_min
                return target_value

            self.values = list(map(_normalize, self.values))
        else:
            # multi-dimensional (vector) values
            mins = [min(value[i] for value in self.values)
                    for i in range(self._values_dimension)]
            maxs = [max(value[i] for value in self.values)
                    for i in range(self._values_dimension)]

            def _normalize(vector):
                v = [
                    (vi - mini) / (maxi - mini)
                    for vi, mini, maxi in zip(vector, mins, maxs)
                ]
                target_vector = tuple(
                    vi * (maxi - mini) + mini
                    for vi, (mini, maxi)
                    in zip(v, self.normalization_range)
                )
                return target_vector

            self.values = list(map(_normalize, self.values))

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

        # get patch collection of background units contours
        if self.background:
            background_kwargs = len(self.background) * [
                {"facecolor": None, "fill": False, "edgecolor": "k"}]
            background_collection = Region.to_mpl_collection(
                regions=self.background, kwargs_list=background_kwargs,
                antialiased=True)

        # make plot
        fig, ax = plt.subplots()
        ax.axis('equal')
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.invert_yaxis()

        # put patches on axes
        ax.add_collection(path_collection)
        if self.background:
            ax.add_collection(background_collection)

    def save_image(self, filepath):
        """ Render plot to file. """
        plt.savefig(filepath)
        plt.close()

    def show(self):
        """ Render plot to window. """
        plt.show()
        plt.close()
