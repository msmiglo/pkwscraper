
# FOR RESEARCH

import json
import os
import random

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import PathPatch, Polygon
from matplotlib.path import Path

from pkwscraper.lib.controller import Controller
from pkwscraper.lib.dbdriver import DbDriver
from pkwscraper.lib.region import Region
from pkwscraper.lib.utilities import get_parent_code
from pkwscraper.lib.visualizer import Colormap, Visualizer


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
                #too_many_absolute
            ])

        # make colormap
        '''
        def colormap(values):
            # unpack measures
            """invalid_percent, too_many_candidates_percent, \
                too_many_absolute = values"""
            invalid_percent, too_many_candidates_percent = values

            # determine color components
            red = too_many_candidates_percent
            green = 1 - invalid_percent
            blue = min(1, max(0, invalid_percent - red))
            alpha = 0.82

            # return color
            return [red, green, blue, alpha]
        '''
        colormap = Colormap(color_data={
            (0., 0.): (0.0, 1.0, 0.0, 0.82),
            (0., 1.): (1.0, 1.0, 0.0, 0.82),
            (1., 0.): (0.0, 0.0, 1.0, 0.82),
            (1., 1.): (1.0, 0.0, 0.0, 0.82),
            #(0.5, 0.5): (0.5, 0.5, 0.0, 0.82),
            (0.5, 1.0): (1.0, 0.5, 0.0, 0.82),
            (0.5, 0.0): (0.0, 0.5, 0.5, 0.82),
            (1.0, 0.5): (0.5, 0.0, 0.5, 0.82),
            (0.0, 0.5): (0.5, 1.0, 0.0, 0.82),
        })

        # make visualizer
        vis = Visualizer(
            regions=gminy_regions,
            values=gminy_values,
            colormap=colormap,
            contours=okregi_regions,
            normalization_range=[(0, 1), (0, 1)]
        )
        vis.normalize_values()
        vis.render_colors()
        vis.prepare()
        vis.show()

        # show max values
        print(f"max invalid votes percentage: {vis.maxs[0]}")
        print(f"max too many candidates percentage: {vis.maxs[1]}")
        #print(f"max too many candidates absolute: {vis.maxs[2]}")


class NewTerritoryVisualizer:
    def visualize_2a(self):
        # make colormap
        '''
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
        '''
        colormap = Colormap(color_data={
            (0., 0.): (0.0, 1.0, 0.0, 0.82),
            (0., 1.): (1.0, 1.0, 0.0, 0.82),
            (1., 0.): (0.0, 0.0, 1.0, 0.82),
            (1., 1.): (1.0, 0.0, 0.0, 0.82),
            (0.5, 1.0): (1.0, 0.5, 0.0, 0.82),
            (0.5, 0.0): (0.0, 0.5, 0.5, 0.82),
            (1.0, 0.5): (0.5, 0.0, 0.5, 0.82),
            (0.0, 0.5): (0.5, 1.0, 0.0, 0.82),
        })

        # define evaluating function
        def function(db):
            # read protocoles data from polling districts from DB
            protocoles = db["protokoły"].find(
                query={},
                fields=["voters", "ballots_valid", "votes_invalid",
                        "invalid_2_candidates", "votes_valid"]
            )

            # initiate sums
            voters = 0
            ballots_valid = 0
            votes_invalid = 0
            invalid_2_candidates = 0
            votes_valid = 0

            # iterate over protocoles and sum votes
            for protocole_record in protocoles:
                voters += protocole_record[0]
                ballots_valid += protocole_record[1]
                votes_invalid += protocole_record[2]
                invalid_2_candidates += protocole_record[3]
                votes_valid += protocole_record[4]

            # calculate measures
            invalid_percent = votes_invalid / ballots_valid
            too_many_candidates_percent = invalid_2_candidates / votes_invalid
            too_many_absolute = invalid_2_candidates / ballots_valid

            # return vector of values
            return invalid_percent, too_many_candidates_percent

        ctrl = Controller(
            ("Sejm", 2015), function, colormap, granularity="communes",
            outlines_granularity="constituencies", normalization=True,
            output_filename="głosy_nieważne.png"
        )
        ctrl.run()

        # show max values
        print(f"max invalid votes percentage: {ctrl.vis.maxs[0]}")
        print(f"max too many candidates percentage: {ctrl.vis.maxs[1]}")
        #print(f"max too many candidates absolute: {ctrl.vis.maxs[2]}")

    def visualize_3(self):
        # define evaluating function
        def function(db):
            # get Razem candidates
            razem_list = db["listy"].find_one(
                {"committee_shortname": "KW Razem"}, fields="_id")
            razem_candidates = db["kandydaci"].find({"list": razem_list})

            # get results on polling districts
            okreg_no = db["okręgi"].find_one({}, fields="number")
            wyniki_tablename = f"wyniki_{okreg_no}"
            wyniki = db[wyniki_tablename].find({})
            obwod_to_protocole = {
                obwod_id: protocole_id
                for protocole_id, obwod_id
                in db["protokoły"].find({}, fields=["_id", "obwod"])
            }

            # sum of votes
            n_obwody = len(wyniki)
            total_votes_valid = 0
            total_votes_razem = 0
            obwody_percents_razem = []

            # iterate over results in polling districts
            for wyniki_id, wyniki_record in wyniki.items():
                obwod_id = wyniki_record["obwod"]
                protocole_id = obwod_to_protocole[obwod_id]
                votes_valid = db["protokoły"][protocole_id]["votes_valid"]
                if votes_valid == 0:
                    continue
                total_votes_valid += votes_valid

                votes_razem = 0
                for candidate_id, votes in wyniki_record.items():
                    if candidate_id in ["_id", "obwod", "candidates_count"]:
                        continue
                    if candidate_id in razem_candidates:
                        votes_razem += votes

                total_votes_razem += votes_razem
                obwody_percents_razem.append(votes_razem / votes_valid)

            # process results
            total_percent_razem = total_votes_razem / total_votes_valid
            mean_percent_razem = sum(obwody_percents_razem) / n_obwody

            # Let's see what is the relation of mean percentage to
            # the total percentage. This can differ because varying
            # size of polling districts. If the mean percentage is greater
            # than total percentage - that means, that Razem got better
            # result in smaller polling districts. If mean percentage is
            # smaller than total percentage - bigger polling districts
            # favoured Razem.
            #
            # Summing up:
            # - ratio > 1.0: Razem is preferred by bigger polling districts
            # - ratio < 1.0: Razem is preferred by smaller polling districts
            return total_percent_razem / mean_percent_razem - 0.5

        # define colormap
        colormap = Colormap("seismic")

        # run controller
        ctrl = Controller(
            ("Sejm", 2015), function, colormap, granularity="województwa",
            outlines_granularity="województwa", normalization=False,
            output_filename="razem_polling_district_size_prefference.png"
        )
        ctrl.run()

    def visualize_4(self):
        # define evaluating function
        def function(db):
            # get Razem candidates
            razem_list = db["listy"].find_one(
                {"committee_shortname": "KW Razem"}, fields="_id")
            razem_candidates = db["kandydaci"].find({"list": razem_list})

            # get results on polling districts
            okreg_no = db["okręgi"].find_one({}, fields="number")
            wyniki_tablename = f"wyniki_{okreg_no}"
            wyniki = db[wyniki_tablename].find({})
            obwod_to_protocole = {
                obwod_id: protocole_id
                for protocole_id, obwod_id
                in db["protokoły"].find({}, fields=["_id", "obwod"])
            }

            # sum of votes
            n_obwody = len(wyniki)
            total_votes_valid = 0
            total_votes_razem = 0
            obwody_percents_razem = []

            # iterate over results in polling districts
            for wyniki_id, wyniki_record in wyniki.items():
                obwod_id = wyniki_record["obwod"]
                protocole_id = obwod_to_protocole[obwod_id]
                votes_valid = db["protokoły"][protocole_id]["votes_valid"]
                if votes_valid == 0:
                    continue
                total_votes_valid += votes_valid

                votes_razem = 0
                for candidate_id, votes in wyniki_record.items():
                    if candidate_id in ["_id", "obwod", "candidates_count"]:
                        continue
                    if candidate_id in razem_candidates:
                        votes_razem += votes

                total_votes_razem += votes_razem
                obwody_percents_razem.append(votes_razem / votes_valid)

            # calculate standard deviations (STD) of votes
            average_votes_razem = total_votes_razem / n_obwody
            average_votes_valid = total_votes_valid / n_obwody
            expected_votes_std = average_votes_razem ** 0.5
            expected_percent_std = expected_votes_std / average_votes_valid
            real_percent_std = np.std(obwody_percents_razem)

            # Let's see what is the dispersion of Razem results compared
            # to expected value. Bigger dispersion can mean that population
            # is more divided geographically. Smaller dispersion can mean
            # the population is more uniform geographically.
            #
            # Summing up:
            # - ratio > 1.0: Razem result varies
            # - ratio < 1.0: Razem result is uniform
            return real_percent_std / expected_percent_std - 1.5

        # define colormap
        colormap = Colormap("seismic")

        for gran in ["województwa", "okręgi", "powiaty", "gminy"]:
            # run controller
            ctrl = Controller(
                ("Sejm", 2015), function, colormap, granularity=gran,
                outlines_granularity="województwa", normalization=True,
                output_filename=f"razem_deviation_difference_{gran}.png"
            )
            ctrl.run()


if __name__ == "__main__":
    new_ter_vis = NewTerritoryVisualizer()
    new_ter_vis.visualize_4()
    #new_ter_vis.visualize_3()
    #new_ter_vis.visualize_2a()

    #ter_vis = TerritoryVisualizer()
    #ter_vis.visualize()
    #ter_vis.visualize_2()
