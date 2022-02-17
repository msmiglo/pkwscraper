
import numpy as np

from pkwscraper.lib.controller import Controller
from pkwscraper.lib.dbdriver import DbDriver
from pkwscraper.lib.visualizer import Colormap

"""
This examples shows the winners of voting in each territorial unit. It
assignes color to each of whole-country committee and then puts the
color of winner on plot. The intensity of color indicates the value of
voting result for this committee.

Color code:
- colors: each committee has its own base color
- white: the winner of voting in this unit got 0% of votes
- base color: the winner in this unit got 50% of votes
- black: the winner of voting in this unit got 100% of votes
- intermediate colors indicates the result of voting for winning list

This test also demonstrates the functionality of limiting analysis to
only one territorial unit.
"""

SEJM_2015_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/preprocessed/"


def function(db):
    # get list number of each candidate
    candidates = db["kandydaci"].find(
        {"is_crossed_out": False}, fields=["_id", "list"])
    candidate_to_list = {
        cand_id: db["listy"][list_id]["list_number"]
        for cand_id, list_id in candidates}

    # list all lists
    lists_ids = set(list_id for _, list_id in candidates)
    lists_numbers = [db["listy"][list_id]["list_number"]
                     for list_id in lists_ids]

    # make results dict
    results = {list_no: 0 for list_no in lists_numbers}

    # get names of results tables
    constituency_nos = db["okręgi"].find({}, fields="number")
    table_names = [f"wyniki_{const_no}" for const_no in constituency_nos]

    # iterate over constituencies
    for table_name in table_names:
        voting_results = db[table_name].find({})
        for result_i in voting_results.values():
            for cand_id in result_i:
                if cand_id in ["_id", "obwod", "candidates_count"]:
                    continue
                list_no = candidate_to_list[cand_id]
                votes = int(result_i[cand_id])
                results[list_no] += votes

    # get winner
    winner_no = max(results, key=results.get)
    max_votes = results[winner_no]
    all_votes = sum(results.values())
    max_result = max_votes / all_votes

    # return results
    return winner_no, max_result


def colormap(values):
    winner_committee, result = values
    if winner_committee == 1:    # pis
        party_color = (65, 3, 96)
    elif winner_committee == 2:  # po
        party_color = (245, 66, 0)
    elif winner_committee == 3:  # razem
        party_color = (178, 150, 195)
    elif winner_committee == 4:  # korwin
        party_color = (246, 221, 63)
    elif winner_committee == 5:  # psl
        party_color = (2, 130, 54)
    elif winner_committee == 6:  # lewica
        party_color = (237, 28, 36)
    elif winner_committee == 7:  # kukiz
        party_color = (70, 70, 70)
    elif winner_committee == 8:  # nowoczesna
        party_color = (3, 100, 182)
    else:                        # other
        party_color = (128, 128, 128)

    party_color = np.array(party_color) / 255
    white = np.array([1.0, 1.0, 1.0])
    black = np.array([0.0, 0.0, 0.0])

    if result > 0.5:
        fraction = 2 * result - 1
        color = fraction * black + (1 - fraction) * party_color
    else:
        fraction = 2 * result
        color = fraction * party_color + (1 - fraction) * white

    color = color.tolist() + [0.82]
    return color


def main():
    grans = ["communes", "districts", "constituencies", "voivodships"]
    names = ["1comm", "2distr", "3const", "4voivod"]

    # whole country
    for gran, name in zip(grans, names):
        print(f"processing {gran}...")
        out_gran = "voivodships" if gran == "voivodships" else "constituencies"
        ctrl_i = Controller(
            ("Sejm", 2015), function, colormap, granularity=gran,
            outlines_granularity=out_gran, normalization=False,
            output_filename=f"winners_{name}.png"
        )
        ctrl_i.run()

    # only mazovian voivodship
    db = DbDriver(SEJM_2015_DATA_DIRECTORY, read_only=True)
    mazovian_id = db["województwa"].find_one(
        {"name": "MAZOWIECKIE"}, fields="_id")
    for gran, name in zip(grans, names):
        print(f"processing {gran}...")
        out_gran = "voivodships" if gran == "voivodships" else "constituencies"
        ctrl_j = Controller(
            ("Sejm", 2015), function, colormap, granularity=gran,
            unit=("voivodships", mazovian_id), outlines_granularity=out_gran,
            normalization=False, output_filename=f"mazovia_winners_{name}.png"
        )
        ctrl_j.run()


if __name__ == "__main__":
    main()
