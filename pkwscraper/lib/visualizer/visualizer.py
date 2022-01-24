
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
from pkwscraper.lib.utilities import get_parent_code, Region


ELECTION_TYPE = "sejm"
YEAR = 2015
RAW_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/raw/"
RESCRIBED_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/rescribed/"
PREPROCESSED_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/preprocessed/"


class Visualizer:
    def __init__(self, db=None):
        if db is None:
            db = DbDriver(PREPROCESSED_DATA_DIRECTORY, read_only=True)
        if not isinstance(db, DbDriver):
            raise TypeError("Please pass an instance of `DbDriver` or `None`.")
        if not db.read_only:
            raise RuntimeError(
                "Please pass `DbDriver` for read only or `None`.")
        self.db = db

    def get_invalid(self):
        gminy_geos = self.db["gminy"].find({}, fields=["_id", "geo"])
        gminy = {
            gmina_id: {
                "_id": gmina_id,
                "geo": Region.from_json(geo).data[0],
                "voters": 0,
                "ballots_valid": 0,
                "votes_invalid": 0,
                "invalid_2_candidates": 0,
                "votes_valid": 0,
            }
            for gmina_id, geo in gminy_geos
        }

        obwod_to_gmina_id = {
            obwod_id: gmina_id
            for obwod_id, gmina_id
            in self.db["obwody"].find(
                query={}, fields=["_id", "gmina"])
        }

        protocoles = self.db["protokoły"].find(
            query={},
            fields=["obwod", "voters", "ballots_valid",
                    "votes_invalid", "invalid_2_candidates", "votes_valid"]
        )

        for protocole_record in protocoles:
            obwod_id = protocole_record[0]
            voters = protocole_record[1]
            ballots_valid = protocole_record[2]
            votes_invalid = protocole_record[3]
            invalid_2_candidates = protocole_record[4]
            votes_valid = protocole_record[5]
            gmina_id = obwod_to_gmina_id[obwod_id]

            gmina = gminy[gmina_id]
            gmina["voters"] += voters
            gmina["ballots_valid"] += ballots_valid
            gmina["votes_invalid"] += votes_invalid
            gmina["invalid_2_candidates"] += invalid_2_candidates
            gmina["votes_valid"] += votes_valid

        return gminy

    def visualize_2(self):
        # get constituencies
        okregi_geo = [okreg["geo"] for _id, okreg
                      in self.db["okręgi"].find({}).items()]
        okregi_regions = [Region.from_json(geo) for geo in okregi_geo]

        # prepare plot
        x_min = min(reg.get_xy_range()["x_min"] for reg in okregi_regions)
        x_max = max(reg.get_xy_range()["x_max"] for reg in okregi_regions)
        y_min = min(reg.get_xy_range()["y_min"] for reg in okregi_regions)
        y_max = max(reg.get_xy_range()["y_max"] for reg in okregi_regions)

        okregi_data = [region.data[0] for region in okregi_regions]

        fig, ax = plt.subplots()
        ax.axis('equal')
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.invert_yaxis()

        patches = []

        # draw constituencies
        for okreg_data in okregi_data:
            if len(okreg_data) == 0:
                continue

            # make path object
            vertices = []
            codes = []
            for line in okreg_data:
                vertices += list(line) + [line[0]]
                n = len(line)
                codes += [Path.MOVETO] + n * [Path.LINETO]
            path = Path(vertices, codes)
            # make patch
            patch = PathPatch(path, facecolor=(0, 0, 0, 0), edgecolor="k")
            patch.set_fill(False)
            patches.append(patch)

        # preprocess gminy
        gminy_measures = []

        for gmina in self.get_invalid().values():
            if len(gmina["geo"]) == 0:
                continue

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
            gminy_measures.append(
                [gmina["geo"], invalid_percent,
                 too_many_candidates_percent, too_many_absolute])

        # take max values for scaling
        max_invalid = max(gmina[1] for gmina in gminy_measures)
        max_too_many = max(gmina[2] for gmina in gminy_measures)
        max_too_many_abs = max(gmina[3] for gmina in gminy_measures)
        print(f"max invalid votes percentage: {max_invalid}")
        print(f"max too many candidates percentage: {max_too_many}")
        print(f"max too many candidates absolute: {max_too_many_abs}")

        # draw gminy
        for geo, invalid_percent, too_many_candidates_percent, \
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

            # make path object
            vertices = []
            codes = []
            for line in geo:
                vertices += list(line) + [line[0]]
                n = len(line)
                codes += [Path.MOVETO] + n * [Path.LINETO]
            path = Path(vertices, codes)
            # make patch
            patch = PathPatch(path, color=color)
            patch.set_fill(True)
            patches.append(patch)

        # make plot
        p = PatchCollection(patches, match_original=True, alpha=0.82)
        ax.add_collection(p)

        plt.show()
        plt.close()

    def visualize(self):
        gminy_geo = [gmina["geo"] for _id, gmina
                     in self.db["gminy"].find({}).items()]
        gminy_geo = [Region.from_json(geo).data[0] for geo in gminy_geo]

        powiaty_geo = [powiat["geo"] for _id, powiat
                     in self.db["powiaty"].find({}).items()]
        powiaty_geo = [Region.from_json(geo).data[0] for geo in powiaty_geo]

        voivod_geo = [voivod["geo"] for _id, voivod
                      in self.db["województwa"].find({}).items()]
        voivod_geo = [Region.from_json(geo).data[0] for geo in voivod_geo]

        okregi_geo = [okreg["geo"] for _id, okreg
                      in self.db["okręgi"].find({}).items()]
        okregi_geo = [Region.from_json(geo).data[0] for geo in okregi_geo]

        x_min = min(p[0] for voivod in voivod_geo for line in voivod for p in line)
        x_max = max(p[0] for voivod in voivod_geo for line in voivod for p in line)
        y_min = min(p[1] for voivod in voivod_geo for line in voivod for p in line)
        y_max = max(p[1] for voivod in voivod_geo for line in voivod for p in line)

        fig, ax = plt.subplots()
        ax.axis('equal')
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.invert_yaxis()

        patches = []

        for level in [gminy_geo, powiaty_geo, voivod_geo, okregi_geo]:
            for unit in level:
                if len(unit) == 0:
                    continue
                #color = random.sample("bcgryk", k=1)[0]
                color = [random.random() for _ in range(3)] + [0]
                print(len(unit), end=" ")

                # make path object
                vertices = []
                codes = []
                for line in unit:
                    vertices += list(line) + [line[0]]
                    n = len(line)
                    codes += [Path.MOVETO] + n * [Path.LINETO]
                path = Path(vertices, codes)
                # make patch
                patch = PathPatch(path, color=color)
                patch.set_fill(True)
                patches.append(patch)

            print()
            print()

        p = PatchCollection(patches, match_original=True, alpha=0.4)
        ax.add_collection(p)

        plt.show()
        plt.close()


if __name__ == "__main__":
    vis = Visualizer()
    #vis.visualize()
    vis.visualize_2()
