
"""
This example shows random coloring of all territorial units in database.
"""

import random

from pkwscraper.lib.dbdriver import DbDriver
from pkwscraper.lib.region import Region
from pkwscraper.lib.visualizer import Visualizer


SEJM_2015_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/preprocessed/"


def main():
    # open DB
    db = DbDriver(SEJM_2015_DATA_DIRECTORY, read_only=True)

    # choose units to visualize
    tables = ["gminy", "powiaty", "województwa", "okręgi"]
    regions = []
    for table_name in tables:
        geos = db[table_name].find({}, fields="geo")
        regions += [Region.from_json(geo) for geo in geos]

    # prepare regions and values
    n = len(regions)
    values = n * [0]
    colormap = lambda x: [random.random() for _ in range(3)] + [0.4]

    # make visualizer
    vis = Visualizer(regions, values, colormap)
    vis.render_colors()
    vis.prepare()
    vis.show()


if __name__ == "__main__":
    main()
