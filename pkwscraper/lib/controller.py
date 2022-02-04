
"""
Concepts dictionary explained:

- user function - the function passed to class that takes data for
    single territorial unit and returns a value or vector of values;
- granularity - level of territorial units at which data will be split
    before passing to the function;

- For more, look for explanation in `visualizer.py`.
"""


class Controller:
    def __init__(self, elections, function, colormap, granularity,
                normalization=True, outlines_granularity,
                 title=None, show_legend=False, show_grid=False,
                 output_file=None):
        """
        output_file - str or None - if None - the result will be
            displayed in new window
        """
        # basic correctness checks
        # get election specific addresses and directories
        #     directories to: raw/rescribed/preprocessed/visualized
        #     data - that is the images are 4th stage of data
        #     processing
        # get election specific scraper and preprocessor
        pass

    def force_download(self):
        pass

    def force_rescribe(self):
        pass

    def force_preprocess(self):
        pass

    def run(self):
        # check if data are available
        # if not - download, rescribe and preprocess
        # split DB into granularity units
        # apply function to each unit
        # normalize values if set
        # apply colormap to values
        # zip regions with colors
        # make patches
        # prepare plot
        # add title, legend, grid, values, etc.
        # render plot to window or file
        pass

    def show_db_schema(self):
        """ Show tables and fields in DB as user guide. """
        pass

    def xxx(self):
        pass

    def xxx(self):
        pass

    def xxx(self):
        pass
