
import os
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

from pkwscraper.lib.region import Region
from pkwscraper.lib.visualizer import Visualizer


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

    integration test:
    - test whole
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

    def test_whole(self):
        """ Integration test. """
        # prepare regions and values
        region_1 = Region.from_json(
            "[[[[0.0, 4.0], [2.0, 4.0], [2.0, 2.0], [0.0, 2.0]]]]")
        region_2 = Region.from_json(
            "[[[[2.0, 0.0], [2.0, 4.0], [4.0, 4.0], [4.0, 0.0]]]]")
        region_3 = Region.from_json(
            "[[[[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0]], "
            "[[0.5, 0.5], [1.5, 0.5], [1.0, 1.5]]]]")
        regions = [region_1, region_2, region_3]
        whole_region = Region.from_json(
            "[[[[0.2, 0.2], [0.2, 3.8], [3.8, 3.8], [3.8, 0.2]]]]")
        values = [0.2, 0.4, 0.3]

        # prepare colormap
        def colormap(value):
            red = 0
            green = 1
            blue = value
            alpha = 0.5
            return (red, green, blue, alpha)

        # create visualizer
        vis = Visualizer(regions, values, colormap, contours=[whole_region],
                         title="Test plot")

        # call preparations
        vis.normalize_values()
        vis.render_colors()
        vis.prepare()

        # save to image
        vis.save_image(self.filepath)

        # check image
        self.assertTrue(os.path.exists(self.filepath))


if __name__ == "__main__":
    main()
