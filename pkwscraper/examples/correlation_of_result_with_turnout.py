
import numpy as np

from pkwscraper.lib.controller import Controller
from pkwscraper.lib.visualizer import Colormap

"""
This example shows the correlation between turnout in communes and
the result for each committee. Only country-wide committees has
been considered. This can indicate where the higher turnout is
favourable for given political party and where it is better for
them when people stay home.

Be aware that this is a little bit overinterpreted. It is not neceserily
accurate that an action to encourage or discourage people to go to
elections would keep the trend. It can be equally true that in units
with negative correlation - more of the party supporters stay home, so
encouraging them to vote could result in result increase. Drawing
conclusions from statistical correlations must be done cautionsly.

Color code:
- blue: positive correlation - the MORE people went voting, the BETTER
    result of analysed committee
- red: negative correlation - the MORE people went voting, the WORSE
    result of analysed committee
- white: no linear correlation - percent of people that went votin did
    NOT affect given committee result
"""

def function(db, list_id):
    # auxiliary indexes
    candidate_ids = db["kandydaci"].find(
        query={"list": list_id, "is_crossed_out": False},
        fields="_id"
    )
    obwod_to_protocole = {
        obwod_id: protocole_id
        for protocole_id, obwod_id
        in db["protokoły"].find({}, fields=["_id", "obwod"])
    }
    list_results = []
    turnouts = []

    # iterate over results
    constituency_no = db["okręgi"].find_one({}, fields="number")
    table_name = f"wyniki_{constituency_no}"
    for results_id, results_record in db[table_name].find({}).items():
        # read number of votes for list
        list_votes = sum(
            int(results_record[c_id])
            for c_id in candidate_ids
        )
        # find protocole
        obwod_id = results_record["obwod"]
        protocole_id = obwod_to_protocole[obwod_id]
        protocole = db["protokoły"][protocole_id]
        # read number of votes and voters
        voters = protocole["voters"]
        votes_valid = protocole["votes_valid"]
        # skip empty polling districts
        if votes_valid == 0:
            continue
        # calculate turnout and list result
        list_result = list_votes / votes_valid
        turnout = votes_valid / voters
        # add measures to lists
        list_results.append(list_result)
        turnouts.append(turnout)

    # compute value of correlation
    my_rho = np.corrcoef(list_results, turnouts)
    # return the value
    return my_rho[0][1]


colormap = Colormap(color_data={
    -5: (20, 30, 100, 230),
    -1: (0, 0, 255, 200),
    0: (255, 255, 255, 255),
    1: (255, 0, 0, 200),
    5: (100, 50, 30, 230),
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
        image_name = f"correlation_turnout_to_result_of_{shortname}.png"

        # prepare concrete function
        function_i = lambda db: function(db, list_id)

        # prepare
        ctrl_i = Controller(
            ("Sejm", 2015), function_i, colormap, granularity="powiaty",
            outlines_granularity="constituencies", normalization=False,
            output_filename=image_name
        )
        ctrl_i.run()


if __name__ == "__main__":
    main()
