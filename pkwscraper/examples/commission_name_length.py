
import numpy as np

from pkwscraper.lib.controller import Controller
from pkwscraper.lib.visualizer import Colormap

"""
This example shows some language-based funny analysis. It takes
the length of commissions name for each polling districts and its
dispersion in each commune.

Color code:
- green: SHORT commission name
- red: LONG commision name
- faint color - means BIG relative dispersion (much different lenghts)
- clear, saturated color - means SMALL dispersion (similar lenghts)
"""

def function(db):
    commission_names = db["obwody"].find({}, fields="commission_name")
    def length(name):
        if name is None:
            return 22
        return len(name)

    names_lenghts = list(map(length, commission_names))
    average = np.average(names_lenghts)
    dispersion = np.std(names_lenghts) / average
    return average, dispersion


colormap = Colormap({
    (0.0, 0.0): (0, 255, 0, 220),
    (0.4, 0.0): (100, 50, 0, 220),
    (0.9, 0.0): (255, 0, 0, 220),

    (0.0, 0.6): (100, 255, 220, 200),
    (1.0, 0.6): (255, 220, 220, 200),

    (-0.1, 1.1): (220, 250, 220, 190),
    (0.5, 1.1): (230, 220, 220, 190),
    (1.1, 1.1): (250, 220, 220, 190),
})


def main():
    ctrl = Controller(
        ("Sejm", 2015), function, colormap, granularity="communes",
        outlines_granularity="voivodships", normalization=True,
        output_filename="commission_names.png"
    )
    ctrl.run()


if __name__ == "__main__":
    main()
