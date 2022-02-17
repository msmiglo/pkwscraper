
import numpy as np

from pkwscraper.lib.controller import Controller
from pkwscraper.lib.visualizer import Colormap

"""
This example shows fraction of votes that was given to first 3
candidates from given list. The smaller this percent is, the more
known are candidates from further positions.

If votes distribution would be equal throughout the lists - that
would indicated some conscious decisions while voting. Voting on
first candidate can indicate that the list consists of weak candidates
and voters are more interested in giving vote on the list itself having
trust for the committee creators.

Color code:
- beige: MANY fraction of votes for first 3 candidates from list
- blue: LITTLE fraction of votes for first 3 candidates from list

Smoothness of values across constituencies mayb indicate that the
candidates are not well-known. Major differences between regions
indicate that different candidates get their support in different
regions, which means that they are well known and strongly connected
to their local communities.

Please take into consideration that list of candidates are the same
throughout single constituency. Some sharp edges in values maybe
effect of a candidate being well known in particular are - for example
she/he is an active politician and is known for some formal operation
or decisions made in relation to given ares, but this is only a guess
and would need further investigation.
"""

def function(db, list_id):
    # get valid candidates
    candidates = db["kandydaci"].find(
        {"is_crossed_out": False, "list": list_id},
        fields=["_id", "position"])

    # split candidates
    top3_candidates_ids = []
    further_candidates = []

    for _id, position in candidates:
        if position <= 3:
            top3_candidates_ids.append(_id)
        else:
            further_candidates.append(_id)

    # determine results table names
    constituency_nos = db["okręgi"].find({}, fields="number")
    table_names = [f"wyniki_{const_no}" for const_no in constituency_nos]

    # get votes sum for categories
    top3_votes = 0
    further_votes = 0

    for table_name in table_names:
        results = db[table_name].find({})
        for result in results.values():
            for cand_id in top3_candidates_ids:
                try:
                    top3_votes += int(result[cand_id])
                except KeyError:
                    pass
            for cand_id in further_candidates:
                try:
                    further_votes += int(result[cand_id])
                except KeyError:
                    pass

    # return non-party result
    return top3_votes / (top3_votes + further_votes)


colormap = Colormap(color_data={
    0.00: (0.0, 0.3, 0.7, 0.82),
    1.00: (0.9, 0.8, 0.8, 0.82),
})


def get_whole_country_lists():
    # load source DB
    temp_ctrl = Controller(
        ("Sejm", 2015), None, None, granularity="communes",
        outlines_granularity="constituencies")
    temp_ctrl._load_db()

    # find list id and constituency for each valid candidate
    candidates_data = temp_ctrl.source_db["kandydaci"].find(
        query={"is_crossed_out": False},
        fields=["constituency", "list"]
    )

    # make list of lists id for each constituency
    okreg_to_list = {}
    for okreg_id, list_id in candidates_data:
        if okreg_id not in okreg_to_list:
            okreg_to_list[okreg_id] = []
        okreg_to_list[okreg_id].append(list_id)

    # remove duplicates
    sets_of_lists = [set(okreg_lists) for okreg_lists
                     in okreg_to_list.values()]

    # get unique whole-country lists ids
    lists_ids = list(set.intersection(*sets_of_lists))

    # get lists data
    lists = {list_id: temp_ctrl.source_db["listy"][list_id]
             for list_id in lists_ids}
    return lists


def main():
    # get whole-country lists
    lists = get_whole_country_lists()

    # iterate over committees
    for list_id, list_record in lists.items():
        # determine name of image
        shortname = list_record["committee_shortname"]
        shortname = shortname.replace('"', '').replace(" ", "_")
        image_name = f"top_3_{shortname}_fraction.png"

        # prepare concrete function
        function_i = lambda db: function(db, list_id)

        # prepare
        ctrl_i = Controller(
            ("Sejm", 2015), function_i, colormap, granularity="gminy",
            outlines_granularity="constituencies", normalization=False,
            output_filename=image_name
        )
        ctrl_i.run()


if __name__ == "__main__":
    main()
