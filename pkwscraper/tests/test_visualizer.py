
from matplotlib.cm import ocean
import matplotlib.pyplot as plt
import numpy as np
import os
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

from pkwscraper.lib.region import Region
from pkwscraper.lib.visualizer import Colormap, Visualizer


class TestColormap(TestCase):
    """
    unit tests:
    - test init
    - test init vector values
    - test init matplotlib colormap
    - test init matplotlib colormap name
    - test 1-D interpolate
    - test N-D interpolate
    - test call
    - test call colormap
    - test call vector
    - test make legend
    """
    def setUp(self):
        self.color_data_1d = {
            0.0: ( 50,  10,  20),
            0.1: (230, 100,  50),
            0.5: (120, 100, 255),
            1.2: (  0, 255, 255),
        }
        self.normalized_color_data_1d = {
            0.0: ( 50 / 255,  10 / 255,  20 / 255),
            0.1: (230 / 255, 100 / 255,  50 / 255),
            0.5: (120 / 255, 100 / 255, 255 / 255),
            1.2: (  0 / 255, 255 / 255, 255 / 255),
        }
        self.color_data_2d = {
            (0.0, 0.0): (1.0, 1.0, 0.0),
            (0.0, 1.0): (0.0, 1.0, 1.0),
            (1.0, 1.0): (1.0, 0.0, 1.0),
            (1.0, 0.0): (0.0, 0.0, 0.0),
        }

    def tearDown(self):
        pass

    def test_init(self):
        with self.assertRaises(ValueError):
            Colormap(self.color_data_1d, interpolation="quadratic")

        cm = Colormap(self.color_data_1d)

        self.assertDictEqual(cm._Colormap__data, {
            0.0: (0.19607843137254902, 0.0392156862745098,
                  0.0784313725490196),
            0.1: (0.9019607843137255, 0.39215686274509803,
                  0.19607843137254902),
            0.5: (0.47058823529411764, 0.39215686274509803, 1.0),
            1.2: (0.0, 1.0, 1.0)
        })
        self.assertEqual(cm.interpolation, "linear")
        self.assertIsNone(cm._vdim)

    def test_init_vector_values(self):
        cm = Colormap(self.color_data_2d, "logarithmic")

        self.assertDictEqual(cm._Colormap__data, self.color_data_2d)
        self.assertEqual(cm.interpolation, "logarithmic")
        self.assertEqual(cm._vdim, 2)

    def test_init_matplotlib_colormap(self):
        cm = Colormap(ocean)

        self.assertIs(cm._Colormap__data, ocean)
        self.assertEqual(cm.interpolation, "linear")
        self.assertIsNone(cm._vdim)

    def test_init_matplotlib_colormap_name(self):
        cm = Colormap("ocean")

        self.assertIs(cm._Colormap__data, ocean)
        self.assertEqual(cm.interpolation, "linear")
        self.assertIsNone(cm._vdim)

    def test_1_d_interpolate(self):
        # arrange
        cm = Colormap.__new__(Colormap)
        cm._Colormap__data = self.normalized_color_data_1d
        # act
        color_1 = cm._1d_interpolate(-1)
        color_2 = cm._1d_interpolate(-0.1)
        color_3 = cm._1d_interpolate(0.0)
        color_4 = cm._1d_interpolate(0.1)
        color_5 = cm._1d_interpolate(0.11)
        color_6 = cm._1d_interpolate(1)
        color_7 = cm._1d_interpolate(1.2)
        color_8 = cm._1d_interpolate(5)
        # assert
        for color, result in [
            (color_1,
             (0.19607843137254902, 0.0392156862745098, 0.0784313725490196)),
            (color_2,
             (0.19607843137254902, 0.0392156862745098, 0.0784313725490196)),
            (color_3,
             (0.19607843137254902, 0.0392156862745098, 0.0784313725490196)),
            (color_4,
             (0.9019607843137255, 0.39215686274509803, 0.19607843137254902)),
            (color_5,
             (0.8911764705882352, 0.39215686274509803, 0.21617647058823528)),
            (color_6,
             (0.13445378151260506, 0.8263305322128852, 1.0)),
            (color_7, (0.0, 1.0, 1.0)),
            (color_8, (0.0, 1.0, 1.0)),
        ]:
            for color_i, result_i in zip(color, result):
                self.assertAlmostEqual(color_i, result_i)

    def test_n_d_interpolate(self):
        # arrange
        cm = Colormap.__new__(Colormap)
        cm._Colormap__data = self.color_data_2d
        # act
        color_1 = cm._nd_interpolate((0.3, 0.8))
        color_2 = cm._nd_interpolate((0.0, 1.0))
        color_3 = cm._nd_interpolate((0.5, 0.2))
        # assert
        for color, result in [
            (color_1, (0.31914294589583, 0.725615282464, 0.770649196451)),
            (color_2, (0.01619069672298, 0.987632500101, 0.987632500101)),
            (color_3, (0.5, 0.5, 0.272459202136)),
        ]:
            for color_i, result_i in zip(color, result):
                self.assertAlmostEqual(color_i, result_i)

    def test_call(self):
        # arrange
        mock_cm = Colormap.__new__(Colormap)
        mock_cm._Colormap__data = MagicMock()
        mock_cm._Colormap__data.return_value = (0, 0.5, 0.5)
        mock_cm._1d_interpolate = MagicMock()
        mock_cm._1d_interpolate.return_value = (1, 1, 1)
        mock_cm._nd_interpolate = MagicMock()
        mock_cm._nd_interpolate.return_value = (0, 0, 0)
        # act
        result = mock_cm(6.2)
        # assert
        self.assertTupleEqual(result, (1, 1, 1))
        mock_cm._Colormap__data.assert_not_called()
        mock_cm._1d_interpolate.assert_called_once_with(6.2)
        mock_cm._nd_interpolate.assert_not_called()

    def test_call_colormap(self):
        # arrange
        mock_cm = Colormap.__new__(Colormap)
        mock_cm._Colormap__data = ocean
        mock_cm._1d_interpolate = MagicMock()
        mock_cm._nd_interpolate = MagicMock()
        # act
        result = mock_cm(0.5)
        result_2 = mock_cm(2)
        # assert
        self.assertTupleEqual(
            result, (0.0, 0.2529411764705882, 0.5019607843137255, 1.0))
        self.assertTupleEqual(result_2, (1, 1, 1, 1))
        mock_cm._1d_interpolate.assert_not_called()
        mock_cm._nd_interpolate.assert_not_called()

    def test_call_vector(self):
        # arrange
        mock_cm = Colormap.__new__(Colormap)
        mock_cm._Colormap__data = MagicMock()
        mock_cm._Colormap__data.return_value = (0, 0.5, 0.5)
        mock_cm._1d_interpolate = MagicMock()
        mock_cm._1d_interpolate.return_value = (1, 1, 1)
        mock_cm._nd_interpolate = MagicMock()
        mock_cm._nd_interpolate.return_value = (0, 0, 0)
        # act
        result = mock_cm((3, 0.2))
        # assert
        self.assertTupleEqual(result, (0, 0, 0))
        mock_cm._Colormap__data.assert_not_called()
        mock_cm._1d_interpolate.assert_not_called()
        mock_cm._nd_interpolate.assert_called_once_with((3, 0.2))

    @skip
    def test_make_legend(self):
        # arrange
        # act
        # assert
        pass


class TestVisualizer(TestCase):
    """
    unit tests:
    - test init
    - test init vector values
    - test normalize values
    - test normalize vector values
    - test render colors
    - test prepare
    - test save image
    - test show
    """
    def setUp(self):
        # mock regions
        mock_region_1 = MagicMock()
        mock_region_1.is_empty.return_value = False
        mock_region_1.get_xy_range.return_value = {
            "x_min": 1.0, "x_max": 4.0, "y_min": 2.0,  "y_max": 5.0}

        mock_region_2 = MagicMock()
        mock_region_2.is_empty.return_value = False
        mock_region_2.get_xy_range.return_value = {
            "x_min": 0.0, "x_max": 3.0, "y_min": 1.0,  "y_max": 8.0}

        self.regions = [mock_region_1, mock_region_2]

        # mock values
        self.values = [0.6, 0.17]

        # mock colors
        self.colors = [(0.1, 0.2, 0.5, 1.0), (0.4, 0.8, 0.3, 1.0)]
        self.colormap = MagicMock()
        self.colormap.side_effect = self.colors

        # test image filepath
        self.filepath = "./image_26333663.png"

    def tearDown(self):
        # remove image if present
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_init(self):
        # act
        with self.assertRaises(ValueError):
            Visualizer(self.regions, [1, 2, 3, 4, 5], self.colormap)
        with self.assertRaises(ValueError):
            Visualizer(self.regions, self.values, self.colormap,
                       normalization_range=[1, 0])
        vis = Visualizer(self.regions, self.values, self.colormap)
        # assert
        self.assertIsNone(vis._vdim)
        self.assertListEqual(vis.regions, self.regions)
        self.assertListEqual(vis.values, self.values)
        self.assertIs(vis.colormap, self.colormap)
        self.assertIsNone(vis.contours)
        self.assertEqual(vis.interpolation, "linear")
        self.assertTupleEqual(vis.normalization_range, (0, 1))
        self.assertIsNone(vis.title)
        self.assertFalse(vis.color_legend)
        self.assertFalse(vis.grid)

    def test_init_vector_values(self):
        vis = Visualizer(
            regions=self.regions,
            values=[(0, 6, 7, 8, 9), (1, 2, 3, 4, 5)],
            colormap=self.colormap
        )
        self.assertEqual(vis._vdim, 5)
        self.assertEqual(len(vis.values), 2)
        self.assertTupleEqual(vis.normalization_range,
                              ((0, 1), (0, 1), (0, 1), (0, 1), (0, 1)))

        vis_2 = Visualizer(
            regions=self.regions,
            values=[(0, 6, 7, 8, 9), (1, 2, 3, 4, 5)],
            colormap=self.colormap,
            normalization_range=[(0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
        )

    def test_normalize_values(self):
        # arrange
        vis = Visualizer(self.regions, self.values, self.colormap,
                         normalization_range=[0.5, 2])
        # act
        result = vis.normalize_values()
        # assert
        self.assertIsNone(result)
        self.assertListEqual(vis.values, [2, 0.5])

    def test_normalize_vector_values(self):
        # arrange
        vis = Visualizer(
            regions=self.regions,
            values=[(0, 6, 7, 8, 9), (1, 2, 3, 4, 5)],
            colormap=self.colormap,
            normalization_range=[2, 5]
        )
        # act
        result = vis.normalize_values()
        # assert
        self.assertIsNone(result)
        self.assertListEqual(vis.values, [[2, 5, 5, 5, 5], [5, 2, 2, 2, 2]])

    def test_render_colors(self):
        # arrange
        vis = Visualizer(self.regions, self.values, self.colormap)
        # act
        result = vis.render_colors()
        # assert
        self.assertIsNone(result)
        self.assertListEqual(vis.colors, self.colors)

    def test_prepare(self):
        # arrange
        mock_2 = self.regions[1]
        vis = Visualizer(self.regions, self.values, self.colormap,
                         contours=[mock_2])
        vis.colors = self.colors
        MockRegionClass = MagicMock()
        mock_ax = MagicMock()
        mock_fig = MagicMock()
        mock_plt = MagicMock()
        mock_plt.subplots.return_value = mock_fig, mock_ax
        # act
        with patch("pkwscraper.lib.visualizer.plt", mock_plt):
            with patch("pkwscraper.lib.visualizer.Region", MockRegionClass):
                result = vis.prepare()
        # assert
        mock_plt.subplots.assert_called_once_with()
        mock_ax.set_xlim.assert_called_once_with(0, 4)
        mock_ax.set_ylim.assert_called_once_with(1, 8)
        self.assertEqual(mock_ax.add_collection.call_count, 2)
        self.assertEqual(
            MockRegionClass.to_mpl_collection.call_count, 2)

    def test_save_image(self):
        # arrange
        mock_vis = MagicMock()
        mock_plt = MagicMock()
        filepath = "./directory/image001.svg"
        # act
        with patch("pkwscraper.lib.visualizer.plt", mock_plt):
            result = Visualizer.save_image(mock_vis, filepath)
        # assert
        self.assertIsNone(result)
        mock_plt.savefig.assert_called_once_with(filepath)
        mock_plt.close.assert_called_once_with()

    def test_show(self):
        # arrange
        mock_vis = MagicMock()
        mock_plt = MagicMock()
        # act
        with patch("pkwscraper.lib.visualizer.plt", mock_plt):
            result = Visualizer.show(mock_vis)
        # assert
        self.assertIsNone(result)
        mock_plt.show.assert_called_once_with()
        mock_plt.close.assert_called_once_with()


class TestVisualizerIntegration(TestCase):
    """
    integration tests:
    - test whole visualizer
    - test with colormap
    """
    def setUp(self):
        # test image filepath
        self.filepath = "./image_26333663.png"
        # color data
        self.color_data_2d = {
            (0.0, 0.0): (1.0, 1.0, 1.0),
            (0.0, 1.0): (1.0, 0.0, 0.0),
            (1.0, 1.0): (0.0, 0.0, 0.0),
            (1.0, 0.0): (0.0, 0.1, 1.0),
            (0.3, 0.6): (0.8, 1.0, 0.2),
            (0.8, 0.8): (0.1, 0.8, 0.9),
        }
        self.black_white_data_2d = {
            (0.0, 0.0): 3*[1],
            (0.0, 1.0): 3*[0],
            (1.0, 1.0): 3*[0.5],
            (1.0, 0.0): 3*[0.5],
            (0.5, 0.2): 3*[0],
            (0.5, 0.8): 3*[1],
        }
        # regions
        region_1 = Region.from_json(
            "[[[[0.0, 4.0], [2.0, 4.0], [2.0, 2.0], [0.0, 2.0]]]]")
        region_2 = Region.from_json(
            "[[[[2.0, 0.0], [2.0, 4.0], [4.0, 4.0], [4.0, 0.0]]]]")
        region_3 = Region.from_json(
            "[[[[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0]], "
            "[[0.5, 0.5], [1.5, 0.5], [1.0, 1.5]]]]")
        self.regions = [region_1, region_2, region_3]
        self.whole_region = Region.from_json(
            "[[[[0.2, 0.2], [0.2, 3.8], [3.8, 3.8], [3.8, 0.2]]]]")

    def tearDown(self):
        # remove image if present
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_whole_visualizer(self):
        # prepare data
        values = [0.2, 0.4, 0.3]

        def colormap(value):
            red = 0
            green = 1
            blue = value
            alpha = 0.5
            return (red, green, blue, alpha)

        # create visualizer
        vis = Visualizer(self.regions, values, colormap,
                         contours=[self.whole_region], title="Test plot")

        # call preparations
        vis.normalize_values()
        vis.render_colors()
        vis.prepare()

        # save to image
        vis.save_image(self.filepath)

        # check image
        self.assertTrue(os.path.exists(self.filepath))

    def test_with_colormap(self):
        # prepare data
        values = [(0.2, 0.5), (0.4, 0.1), (0.3, 1.0)]
        colormap = Colormap(self.color_data_2d)

        # create visualizer
        vis = Visualizer(self.regions, values, colormap,
                         contours=[self.whole_region], title="Test plot")

        # call preparations
        vis.normalize_values()
        vis.render_colors()

    #@skip
    def test_rendering_color_space(self):
        """
        This test saves an image of color space
        """
        # prepare directory
        if not os.path.exists("./research/color spaces benchmarks/"):
            os.makedirs("./research/color spaces benchmarks/")

        for name, colordata in zip(
            ["color", "black_white"],
            [self.color_data_2d, self.black_white_data_2d]
        ):
            # make roughly unique hash of code version by computing common
            # bytes sum times alternating sum
            with open("./pkwscraper/lib/visualizer.py", "rb") as f:
                code = f.read()
            code_hash = sum(code) * sum(c ^ 0b01010101 for c in code)

            # compose filepath
            filepath = (f"./research/color spaces benchmarks"
                        f"/_benchmark_{name}_{code_hash}.png")

            # make color space
            size = 50 # 250
            cm = Colormap(colordata)
            space = np.array([[cm([j, i])
                               for j in np.linspace(0, 1, size + 1)]
                              for i in np.linspace(0, 1, size + 1)])
            plt.imshow(space, origin='lower')
            plt.savefig(filepath)
            #plt.show()
            plt.close()


if __name__ == "__main__":
    main()
