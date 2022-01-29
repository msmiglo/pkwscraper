
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

        # prepare path patches
        n = len(regions)

        kwargs_list = [
            {"color": [random.random() for _ in range(3)] + [0]}
            for i in range(n)
        ]

        path_collection = Region.to_mpl_collection(
            regions=regions, kwargs_list=kwargs_list, alpha=0.4)

        # get plot range
        ranges = [region.get_xy_range()
                  for region in regions
                  if not region.is_empty()]

        x_min = min(r["x_min"] for r in ranges)
        x_max = max(r["x_max"] for r in ranges)
        y_min = min(r["y_min"] for r in ranges)
        y_max = max(r["y_max"] for r in ranges)


        # make plot
        fig, ax = plt.subplots()
        ax.axis('equal')
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.invert_yaxis()

        ax.add_collection(path_collection)

        plt.show()
        plt.close()

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

        okregi_kwargs = len(okregi_regions) * [
            {"facecolor": None, "fill": False, "edgecolor": "k"}]

        # preprocess gminy
        gminy_data = self.get_invalid()
        gminy = [
            gmina
            for gmina in gminy_data.values()
            if not gmina["region"].is_empty()
        ]
        gminy_regions = [gmina["region"] for gmina in gminy]
        gminy_measures = []

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
            gminy_measures.append([
                invalid_percent,
                too_many_candidates_percent,
                too_many_absolute
            ])

        # take max values for scaling
        max_invalid = max(gmina[0] for gmina in gminy_measures)
        max_too_many = max(gmina[1] for gmina in gminy_measures)
        max_too_many_abs = max(gmina[2] for gmina in gminy_measures)
        print(f"max invalid votes percentage: {max_invalid}")
        print(f"max too many candidates percentage: {max_too_many}")
        print(f"max too many candidates absolute: {max_too_many_abs}")

        # prepare gminy visualization
        gminy_kwargs = []

        for invalid_percent, too_many_candidates_percent, \
                too_many_absolute in gminy_measures:

            # scale values
            invalid_percent /= max_invalid
            too_many_candidates_percent /= max_too_many
            too_many_absolute /= max_too_many_abs

            # determine color
            red = too_many_candidates_percent
            green = 1 - invalid_percent
            blue = min(1, max(0, invalid_percent - red))

            color = [red, green, blue]
            gminy_kwargs.append({"color": color})

        # make patches for ploting
        gminy_collection = Region.to_mpl_collection(
            regions=gminy_regions, kwargs_list=gminy_kwargs, alpha=0.82)
        okregi_collection = Region.to_mpl_collection(
            regions=okregi_regions, kwargs_list=okregi_kwargs)

        # prepare plot
        x_min = min(reg.get_xy_range()["x_min"] for reg in okregi_regions)
        x_max = max(reg.get_xy_range()["x_max"] for reg in okregi_regions)
        y_min = min(reg.get_xy_range()["y_min"] for reg in okregi_regions)
        y_max = max(reg.get_xy_range()["y_max"] for reg in okregi_regions)

        # make plot
        fig, ax = plt.subplots()
        ax.axis('equal')
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.invert_yaxis()

        ax.add_collection(gminy_collection)
        ax.add_collection(okregi_collection)

        # show plot
        plt.show()
        plt.close()


if __name__ == "__main__":
    ter_vis = TerritoryVisualizer()
    ter_vis.visualize()
    ter_vis.visualize_2()
