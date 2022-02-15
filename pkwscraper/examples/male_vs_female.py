
from pkwscraper.lib.controller import Controller
from pkwscraper.lib.visualizer import Colormap

"""
This example shows fraction of votes that was given to women on
different granularity levels.
"""

def function(db):
    # get candidates divided by gender
    female_ids = db["kandydaci"].find(
        {"gender": "K"}, fields="_id")
    male_ids = db["kandydaci"].find(
        {"gender": "M"}, fields="_id")

    # determine results table name
    constituency_nos = db["okręgi"].find({}, fields="number")
    table_names = [f"wyniki_{const_no}" for const_no in constituency_nos]

    # get votes sum for candidates
    female_votes = 0
    male_votes = 0
    for table_name in table_names:
        results = db[table_name].find({})
        for result in results.values():
            for cand_id in female_ids:
                try:
                    female_votes += int(result[cand_id])
                except KeyError:
                    pass
            for cand_id in male_ids:
                try:
                    male_votes += int(result[cand_id])
                except KeyError:
                    pass

    # return females result
    return female_votes / (female_votes + male_votes)


colormap = Colormap(color_data={
    0.0: (0.0, 0.6, 0.9, 0.82),
    0.5: (1.0, 1.0, 1.0, 0.82),
    1.0: (1.0, 0.6, 0.7, 0.82),
})

def main():
    grans = ["communes", "districts", "constituencies", "voivodships"]
    names = ["1comm", "2distr", "3const", "4voivod"]

    for gran, name in zip(grans, names):
        print(f"processing {gran}...")
        out_gran = "voivodships" if gran == "voivodships" else "constituencies"
        ctrl_i = Controller(
            ("Sejm", 2015), function, colormap, granularity=gran,
            outlines_granularity=out_gran, normalization=False,
            output_filename=f"male_vs_female_{name}.png"
        )
        ctrl_i.run()


if __name__ == "__main__":
    main()
