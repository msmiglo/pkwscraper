
from pkwscraper.lib.controller import Controller
from pkwscraper.lib.visualizer import Colormap

"""
This example shows fraction of votes that was given to candidates that
not belong to political parties. They are probably less known or occupy
worse position on lists, because of their negotiative power. That could
mean that high value of this measure can indicate population with more
political knowledge, or the other way - that political parties and their
local members in the region are widely compromised or disliked.

Color code:
- red: MANY votes on non-party members
- light gray: LITTLE votes on non-party members
"""

def function(db):
    # get valid candidates
    candidates = db["kandydaci"].find(
        {"is_crossed_out": False}, fields=["_id", "party"])

    # split candidates
    non_party_candidates_ids = []
    political_party_candidates = []

    for _id, party in candidates:
        if party.startswith("nie należy do partii politycznej"):
            non_party_candidates_ids.append(_id)
        else:
            political_party_candidates.append(_id)

    # determine results table names
    constituency_nos = db["okręgi"].find({}, fields="number")
    table_names = [f"wyniki_{const_no}" for const_no in constituency_nos]

    # get votes sum for categories
    non_party_votes = 0
    political_party_votes = 0

    for table_name in table_names:
        results = db[table_name].find({})
        for result in results.values():
            for cand_id in non_party_candidates_ids:
                try:
                    non_party_votes += int(result[cand_id])
                except KeyError:
                    pass
            for cand_id in political_party_candidates:
                try:
                    political_party_votes += int(result[cand_id])
                except KeyError:
                    pass

    # return non-party result
    return non_party_votes / (non_party_votes + political_party_votes)


colormap = Colormap(color_data={
    0.00: (0.7, 0.8, 0.8, 0.82),
    1.00: (1.0, 0.1, 0.1, 0.82),
})


def main():
    grans = ["communes", "districts", "constituencies", "voivodships"]
    names = ["1comm", "2distr", "3const", "4voivod"]

    for gran, name in zip(grans, names):
        print(f"processing {gran}...")
        out_gran = "voivodships" if gran == "voivodships" else "constituencies"
        ctrl_i = Controller(
            ("Sejm", 2015), function, colormap, granularity=gran,
            outlines_granularity=out_gran, normalization=True,
            output_filename=f"non_party_fraction_{name}.png"
        )
        ctrl_i.run()

        min_value = ctrl_i.vis.mins
        max_value = ctrl_i.vis.maxs
        if min_value is not None and max_value is not None:
            print(f"Non-party members voting results range from"
                  f" {round(100*min_value, 1)} % to"
                  f" {round(100*max_value, 1)} %.")
            print()


if __name__ == "__main__":
    main()
