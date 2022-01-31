
# FOR RESEARCH

import json
import os
import random

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import PathPatch, Polygon
from matplotlib.path import Path

from pkwscraper.lib.dbdriver import DbDriver
from pkwscraper.lib.region import Region
from pkwscraper.lib.utilities import get_parent_code
from pkwscraper.lib.visualizer import Visualizer


ELECTION_TYPE = "sejm"
YEAR = 2015
RAW_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/raw/"
RESCRIBED_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/rescribed/"
PREPROCESSED_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/preprocessed/"


class TerritoryVisualizer:
    def __init__(self, db=None):
        if db is None:
            db = DbDriver(PREPROCESSED_DATA_DIRECTORY, read_only=True)
        if not isinstance(db, DbDriver):
            raise TypeError("Please pass an instance of `DbDriver` or `None`.")
        if not db.read_only:
            raise RuntimeError(
                "Please pass `DbDriver` for read only or `None`.")
        self.db = db

    def visualize(self):
        # choose units to visualize
        tables = ["gminy", "powiaty", "województwa", "okręgi"]
        regions = []
        for table_name in tables:
            geos = self.db[table_name].find({}, fields="geo")
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

    def get_invalid(self):
        # read communes data from DB
        gminy_data = self.db["gminy"].find({}, fields=["_id", "geo"])
        gminy = {
            gmina_id: {
                "region": Region.from_json(geo),
                "voters": 0,
                "ballots_valid": 0,
                "votes_invalid": 0,
                "invalid_2_candidates": 0,
                "votes_valid": 0,
            }
            for gmina_id, geo in gminy_data
        }

        # read protocoles data from polling districts from DB
        protocoles = self.db["protokoły"].find(
            query={},
            fields=["obwod", "voters", "ballots_valid",
                    "votes_invalid", "invalid_2_candidates", "votes_valid"]
        )

        # iterate over protocoles
        for protocole_record in protocoles:
            # unzip data
            obwod_id = protocole_record[0]
            voters = protocole_record[1]
            ballots_valid = protocole_record[2]
            votes_invalid = protocole_record[3]
            invalid_2_candidates = protocole_record[4]
            votes_valid = protocole_record[5]

            # get commune entry
            gmina_id = self.db["obwody"][obwod_id]["gmina"]
            gmina = gminy[gmina_id]

            # add votes for commune entry
            gmina["voters"] += voters
            gmina["ballots_valid"] += ballots_valid
            gmina["votes_invalid"] += votes_invalid
            gmina["invalid_2_candidates"] += invalid_2_candidates
            gmina["votes_valid"] += votes_valid

        return gminy

    def visualize_2(self):
        # get constituencies
        okregi_regions = [
            Region.from_json(geo)
            for geo
            in self.db["okręgi"].find(
                query={}, fields="geo")
        ]

        # preprocess gminy
        gminy_data = self.get_invalid()
        gminy = [
            gmina
            for gmina in gminy_data.values()
            if not gmina["region"].is_empty()
        ]
        gminy_regions = [gmina["region"] for gmina in gminy]
        gminy_values = []

        for gmina in gminy:
            # calculate measures
            voters = gmina["voters"]
            ballots_valid = gmina["ballots_valid"]
            votes_invalid = gmina["votes_invalid"]
            invalid_2_candidates = gmina["invalid_2_candidates"]
            votes_valid = gmina["votes_valid"]

            invalid_percent = votes_invalid / ballots_valid
            too_many_candidates_percent = invalid_2_candidates / votes_invalid
            too_many_absolute = invalid_2_candidates / ballots_valid

            # add element
            gminy_values.append([
                invalid_percent,
                too_many_candidates_percent,
                too_many_absolute
            ])

        # take max values
        max_invalid = max(gmina[0] for gmina in gminy_values)
        max_too_many = max(gmina[1] for gmina in gminy_values)
        max_too_many_abs = max(gmina[2] for gmina in gminy_values)
        print(f"max invalid votes percentage: {max_invalid}")
        print(f"max too many candidates percentage: {max_too_many}")
        print(f"max too many candidates absolute: {max_too_many_abs}")

        # make colormap
        def colormap(values):
            # unpack measures
            invalid_percent, too_many_candidates_percent, \
                too_many_absolute = values

            # determine color components
            red = too_many_candidates_percent
            green = 1 - invalid_percent
            blue = min(1, max(0, invalid_percent - red))
            alpha = 0.82

            # return color
            return [red, green, blue, alpha]

        # make visualizer
        vis = Visualizer(
            regions=gminy_regions,
            values=gminy_values,
            colormap=colormap,
            background=okregi_regions,
            normalization_range=[(0, 1), (0, 1), (0, 1)]
        )
        vis.normalize_values()
        vis.render_colors()
        vis.prepare()
        vis.show()


if __name__ == "__main__":
    ter_vis = TerritoryVisualizer()
    ter_vis.visualize()
    ter_vis.visualize_2()
