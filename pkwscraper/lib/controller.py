
import json
import os

from pkwscraper.lib.dbdriver import DbDriver
from pkwscraper.lib.elections import Elections
from pkwscraper.lib.region import Region
from pkwscraper.lib.visualizer import Visualizer

"""
Concepts explained:

- user function / function - the function passed to Controller that
    takes data for single territorial unit and returns a value or vector
    of values;
- granularity - level of territorial units at which data will be split
    before passing to the function;
- downloading and scraping - first stage of data processing - obtaining
    raw data from internet, it includes rescribing to DB tables;
- preprocessing - cleaning rescribed data, making them ready to use
    by visualizing step;
- visualizing - taking preprocessed data and making plots with it;

- For more, look for explanation in `visualizer.py`.
"""


GRANULARITY_DICT = {
    "voivodships": "województwa",
    "constituencies": "okręgi",
    "districts": "powiaty",
    "communes": "gminy",
}


class Controller:
    """
    This is the main class of the project, that calls all steps
    of data processing. This is created by passing main parameters
    and, most importantly, evaluating function. This renders a plot
    to image or for showing in separate window.
    """
    def __init__(self, elections, function, colormap, granularity,
                outlines_granularity=None, normalization=True,
                 title=None, show_legend=False, show_grid=False,
                 output_filename=None, interpolation='linear'):
        """
        Constructor does basic checks and creates class attributes.

        elections: (str, int) - type and year (unambiguous identifier)
            of elections,
        function: callable - function to evaluate data for single unit,
        colormap: callable - function or object that converts numerical
            values returned by function to proper colors,
        granularity: str - the level of territorial units that plot
            will be split into,
        outlines_granularity - level of territorial units that borders
            will be placed on top of plot as contours,
        normalization: bool - whether or not values from all units
            should be scaled to (0,1) range before passing to colormap,
        title: str - title of plot that is placed over the plot,
        show_legend: bool - whether or not to show the color key in
            form of legend, can contain extreme values written next
            to it,
        show_grid: bool - whether or not to show the frame around
            the units plot,
        output_filename: str or None - if None - the result will be
            displayed in new window, otherwise, it will be rendered to
            image file saved to given filenam in default visualizing
            directory,
        interpolation: str - method of interpolation of colors in the
            colormap.
        """
        # translate English variants of arguments
        if granularity in GRANULARITY_DICT:
            granularity = GRANULARITY_DICT[granularity]
        if outlines_granularity in GRANULARITY_DICT:
            outlines_granularity = GRANULARITY_DICT[outlines_granularity]

        # basic correctness checks
        if granularity not in GRANULARITY_DICT.values():
            raise ValueError(
                '`granularity` should be one of: "voivodships", '
                '"constituencies" or "districts", "communes"')

        if outlines_granularity not in GRANULARITY_DICT.values():
            raise ValueError(
                '`outlines_granularity` should be one of: "voivodships", '
                '"constituencies" or "districts", "communes"')

        if not isinstance(elections, tuple) or len(elections) != 2:
            raise TypeError("Please, provide elections identifier: (type, year).")

        # assing arguments
        elections_type, year = elections
        self.elections = Elections(elections_type=elections_type, year=year)
        self.function = function
        self.colormap = colormap
        self.granularity = granularity
        self.outlines_granularity = outlines_granularity
        self.normalization = normalization
        self.title = title
        self.show_legend = show_legend
        self.show_grid = show_grid
        self.output_filename = output_filename
        self.interpolation = interpolation
        self.vis = None
        self.source_db = None

    def _scrape(self):
        _ScraperClass = self.elections.get_scraper_class()
        scraper = _ScraperClass()
        scraper.run_all()

    def _preprocess(self):
        _PreprocessingClass = self.elections.get_preprocessing_class()
        preprocessing = _PreprocessingClass()
        preprocessing.run_all()

    def _load_db(self):
        try:
            # try opening preprocessed db
            DbDriver(self.elections.preprocessed_dir, read_only=True)
        except IOError:
            try:
                # preprocessed db cannot be opened, check if there is rescribed db
                DbDriver(self.elections.rescribed_dir, read_only=True)
            except IOError:
                # rescribed db cannot be opened, run downloading and scraping
                self._scrape()
            # rescribed db present, run preprocessing
            self._preprocess()
        # preprocessed db present, load it
        self.source_db = DbDriver(self.elections.preprocessed_dir, read_only=True)

    def _split_db(self):
        """
        This is used to split data in DB to correspond only to the
        single unit of analysis. Function passed by user can use all
        the DB instance data given to it, and be sure that they are
        isolated from data corresponding to other units.
        """
        units = self.source_db[self.granularity].find({})
        db_refs = DbReferences(self.source_db, self.granularity)

        for unit_id in units:
            # get IDs of records in tables
            gmina_ids = db_refs.get_gmina(unit_id)
            powiat_ids = db_refs.get_powiat(unit_id)
            okreg_ids = db_refs.get_okreg(unit_id)
            voivodship_ids = db_refs.get_voivodship(unit_id)
            obwody_ids = db_refs.get_obwod(unit_id)
            protocole_ids = db_refs.get_protocole(unit_id)
            list_ids = db_refs.get_list(unit_id)
            candidate_ids = db_refs.get_candidate(unit_id)
            mandate_ids = db_refs.get_mandate(unit_id)
            wyniki_ids = db_refs.get_wyniki(unit_id)

            tables_and_ids = {
                "gminy": gmina_ids,
                "powiaty": powiat_ids,
                "okręgi": okreg_ids,
                "województwa": voivodship_ids,
                "obwody": obwody_ids,
                "protokoły": protocole_ids,
                "listy": list_ids,
                "kandydaci": candidate_ids,
                "mandaty": mandate_ids
            }
            tables_and_ids.update(wyniki_ids)

            # create db driver instance
            db = DbDriver.__new__(DbDriver)
            db._DbDriver__read_only = False
            db._DbDriver__tables = {}
            db._DbDriver__dropped_tables = []

            # copy records
            for table_name, ids_list in tables_and_ids.items():
                db.create_table(table_name)
                for _id in ids_list:
                    record = self.source_db[table_name][_id]
                    db[table_name].put(dict(record), _id=_id)

            # freeze db and conclude iteration
            db._DbDriver__read_only = True
            yield db

    def _visualize(self):
        # split db into units
        dbs = self._split_db()

        # process data
        regions = []
        values = []

        for db in dbs:
            # make region
            geo = db[self.granularity].find_one({}, fields="geo")
            region = Region.from_json(geo)
            regions.append(region)

            # evaluate value
            value = self.function(db)
            values.append(value)

        # determine outline units
        outline_geos = self.source_db[self.outlines_granularity].find({}, fields="geo")
        outline_regions = [Region.from_json(geo) for geo in outline_geos]

        # make visualizer object
        self.vis = Visualizer(
            regions, values, self.colormap, contours=outline_regions,
            interpolation=self.interpolation, title=self.title,
            color_legend=self.show_legend, grid=self.show_grid
        )

        # normalize values if set
        if self.normalization:
            self.vis.normalize_values()

        # apply colormap to values
        self.vis.render_colors()

        # prepare plot
        self.vis.prepare()

        ### TODO # add title, legend, grid, values, etc.

        # render plot to window or file
        if self.output_filename:
            visualized_dir = self.elections.visualized_dir
            if not os.path.exists(visualized_dir):
                ### TODO - make image dir, not only main dir
                os.makedirs(visualized_dir)
            output_path = visualized_dir + self.output_filename
            self.vis.save_image(output_path)
        else:
            self.vis.show()

    def run(self):
        """
        Run prepared analysis object. It first makes sure the DB is
        ready to use, or loads it and possibly runs preprocessing/etc.
        """
        self._load_db()
        self._visualize()

    def show_db_schema(self):
        """ Show tables and fields in DB as user guide. """
        raise NotImplementedError("TODO")
        return {tables: {columns: [values_type / enumerating]}}
        pass


class DbReferences:
    """
    This class is making indexes on relations between tables in DB.
    It is needed for pure performance requirements. This class could be
    discarded if the custom DB driver used in this project would have
    indexes implemented and be optimized for performance.

    It assumes that splitting DB would need to get only those records
    from tables, that corresponds to the given territorial unit. That
    causes good hermetization of data and allows to easily avoid bugs
    and mistakes in user-defined function.
    """
    @staticmethod
    def _inverse_dict(dictionary):
        """
        Take dictionary of keys and lists of values and turn it
        to dictionary of values with assigned lists of keys which
        are paired in original dictionary.

        dictionary: dict of {key: [value_1, value_2, ..., value_n]}
        """
        values = []
        for value_list in dictionary.values():
            values += value_list

        inversed_dict = {value: [] for value in values}
        for key, value_list in dictionary.items():
            for value in value_list:
                inversed_dict[value].append(key)

        return inversed_dict

    def __init__(self, source_db, granularity):
        """
        This object makes reading DB relations easier. Each of 4
        granularity levels has to have assigned corresponding records
        IDs for all tables in DB.

        Explicitly saying - there are indexes needed that makes
        assignment from:
            - voivodships
            - constituencies
            - district
            - communes
        to list of:
            - voivodships
            - constituencies
            - districts
            - communes
            - polling districts
            - protocoles
        which they are associated with.

        Alse intermediate assignments are needed from constituencies to:
        - candidates
        - lists
        - mandates
        The latter IDs are determined dynamically during calling
        methods, because the lists of values for each unit within
        one constituency would be the same.

        Voting results IDs are dynamically determined.
        """
        print("Creating indexes for data...")

        self.granularity = granularity

        # auxiliary indexes and names lists
        self._voivodships = source_db["województwa"].find({}, fields="_id")
        self._okregi = source_db["okręgi"].find({}, fields="_id")
        self._gminy = source_db["gminy"].find({}, fields="_id")
        self._wyniki_table_names = {
            okreg_id: f"wyniki_{okreg_no}"
            for okreg_id, okreg_no
            in source_db["okręgi"].find({}, fields=["_id", "number"])
        }
        obwod_to_protocole = {
            obwod_id: protocole_id
            for protocole_id, obwod_id
            in source_db["protokoły"].find({}, fields=["_id", "obwod"])
        }

        # direct indexes
        self._gmina_to_powiat = {
            gmina_id: [powiat_id]
            for gmina_id, powiat_id
            in source_db["gminy"].find({}, fields=["_id", "parent"])
        }

        self._powiat_to_voivodship = {
            powiat_id: [voivodship_id]
            for powiat_id, voivodship_id
            in source_db["powiaty"].find({}, fields=["_id", "parent"])
        }

        self._okreg_to_powiat = {
            okreg_id: json.loads(powiaty)
            for okreg_id, powiaty
            in source_db["okręgi"].find({}, fields=["_id", "powiat_list"])}

        self._powiat_to_okreg = self._inverse_dict(self._okreg_to_powiat)

        self._gmina_to_okreg = {}
        for gmina_id in self._gminy:
            powiat_id = self._gmina_to_powiat[gmina_id][0]
            okreg_id = self._powiat_to_okreg[powiat_id][0]
            self._gmina_to_okreg[gmina_id] = [okreg_id]

        self._gmina_to_voivodship = {}
        for gmina_id in self._gminy:
            powiat_id = self._gmina_to_powiat[gmina_id][0]
            voivodship_id = self._powiat_to_voivodship[powiat_id][0]
            self._gmina_to_voivodship[gmina_id] = [voivodship_id]

        self._okreg_to_voivodship = {}
        for okreg_id in self._okregi:
            powiat_id = self._okreg_to_powiat[okreg_id][0]
            voivodship_id = self._powiat_to_voivodship[powiat_id][0]
            self._okreg_to_voivodship[okreg_id] = [voivodship_id]

        self._powiat_to_gmina = self._inverse_dict(self._gmina_to_powiat)

        self._okreg_to_gmina = self._inverse_dict(self._gmina_to_okreg)

        self._voivodship_to_gmina = self._inverse_dict(self._gmina_to_voivodship)

        self._voivodship_to_powiat = self._inverse_dict(
            self._powiat_to_voivodship)

        self._voivodship_to_okreg = self._inverse_dict(self._okreg_to_voivodship)

        self._gmina_to_obwod = {
            gmina_id: [] for gmina_id in self._gminy}
        for obwod_id, gmina_id \
                in source_db["obwody"].find({}, fields=["_id", "gmina"]):
            self._gmina_to_obwod[gmina_id].append(obwod_id)

        self._powiat_to_obwod = {}
        for powiat_id, gminy in self._powiat_to_gmina.items():
            obwody = []
            for gmina_id in gminy:
                obwody += self._gmina_to_obwod[gmina_id]
            self._powiat_to_obwod[powiat_id] = obwody

        self._okreg_to_obwod = {}
        for okreg_id, powiaty in self._okreg_to_powiat.items():
            obwody = []
            for powiat_id in powiaty:
                obwody += self._powiat_to_obwod[powiat_id]
            self._okreg_to_obwod[okreg_id] = obwody

        self._voivodship_to_obwod = {}
        for voivodship_id, okregi in self._voivodship_to_okreg.items():
            obwody = []
            for okreg_id in okregi:
                obwody += self._okreg_to_obwod[okreg_id]
            self._voivodship_to_obwod[voivodship_id] = obwody

        self._gmina_to_protocole = {
            gmina_id: [obwod_to_protocole[obwod_id] for obwod_id in obwody]
            for gmina_id, obwody in self._gmina_to_obwod.items()
        }

        self._powiat_to_protocole = {
            powiat_id: [obwod_to_protocole[obwod_id] for obwod_id in obwody]
            for powiat_id, obwody in self._powiat_to_obwod.items()
        }

        self._okreg_to_protocole = {
            okreg_id: [obwod_to_protocole[obwod_id] for obwod_id in obwody]
            for okreg_id, obwody in self._okreg_to_obwod.items()
        }

        self._voivodship_to_protocole = {
            voivodship_id: [obwod_to_protocole[obwod_id] for obwod_id in obwody]
            for voivodship_id, obwody in self._voivodship_to_obwod.items()
        }

        # intermediate indexes
        candidates = source_db["kandydaci"].find({})  # maybe add `{"is_crossed_out": False}` ?
        self._okreg_to_candidate = {okreg_id: [] for okreg_id in self._okregi}
        self._okreg_to_list = {okreg_id: [] for okreg_id in self._okregi}
        self._okreg_to_mandate = {okreg_id: [] for okreg_id in self._okregi}

        for candidate_id, candidate in candidates.items():
            okreg_id = candidate["constituency"]
            list_id = candidate["list"]
            self._okreg_to_candidate[okreg_id].append(candidate_id)
            self._okreg_to_list[okreg_id].append(list_id)

        for okreg_id in self._okreg_to_list:
            lists_list = self._okreg_to_list[okreg_id]
            lists_list = list(set(lists_list))
            self._okreg_to_list[okreg_id] = lists_list

        for mandate_id, candidate_id in source_db["mandaty"].find(
                {}, fields=["_id", "candidate"]):
            okreg_id = candidates[candidate_id]["constituency"]
            self._okreg_to_mandate[okreg_id].append(mandate_id)

        # results IDs
        self._obwod_to_table_name = {}
        for obwod_id, okreg_id in source_db["obwody"].find(
                {}, fields=["_id", "constituency"]):
            table_name_i = self._wyniki_table_names[okreg_id]
            self._obwod_to_table_name[obwod_id] = table_name_i

        self._obwod_to_wyniki = {}
        for table_name_i in self._wyniki_table_names.values():
            for wyniki_id, obwod_id in source_db[table_name_i].find(
                    {}, fields=["_id", "obwod"]):
                self._obwod_to_wyniki[obwod_id] = wyniki_id

        print("Indexes for data created.")
        print()

    def get_gmina(self, unit_id):
        if self.granularity == "gminy":
            return [unit_id]
        elif self.granularity == "powiaty":
            return self._powiat_to_gmina[unit_id]
        elif self.granularity == "okręgi":
            return self._okreg_to_gmina[unit_id]
        elif self.granularity == "województwa":
            return self._voivodship_to_gmina[unit_id]

    def get_powiat(self, unit_id):
        if self.granularity == "gminy":
            return self._gmina_to_powiat[unit_id]
        elif self.granularity == "powiaty":
            return [unit_id]
        elif self.granularity == "okręgi":
            return self._okreg_to_powiat[unit_id]
        elif self.granularity == "województwa":
            return self._voivodship_to_powiat[unit_id]

    def get_okreg(self, unit_id):
        if self.granularity == "gminy":
            return self._gmina_to_okreg[unit_id]
        elif self.granularity == "powiaty":
            return self._powiat_to_okreg[unit_id]
        elif self.granularity == "okręgi":
            return [unit_id]
        elif self.granularity == "województwa":
            return self._voivodship_to_okreg[unit_id]

    def get_voivodship(self, unit_id):
        if self.granularity == "gminy":
            return self._gmina_to_voivodship[unit_id]
        elif self.granularity == "powiaty":
            return self._powiat_to_voivodship[unit_id]
        elif self.granularity == "okręgi":
            return self._okreg_to_voivodship[unit_id]
        elif self.granularity == "województwa":
            return [unit_id]

    def get_obwod(self, unit_id):
        if self.granularity == "gminy":
            return self._gmina_to_obwod[unit_id]
        elif self.granularity == "powiaty":
            return self._powiat_to_obwod[unit_id]
        elif self.granularity == "okręgi":
            return self._okreg_to_obwod[unit_id]
        elif self.granularity == "województwa":
            return self._voivodship_to_obwod[unit_id]

    def get_protocole(self, unit_id):
        if self.granularity == "gminy":
            return self._gmina_to_protocole[unit_id]
        elif self.granularity == "powiaty":
            return self._powiat_to_protocole[unit_id]
        elif self.granularity == "okręgi":
            return self._okreg_to_protocole[unit_id]
        elif self.granularity == "województwa":
            return self._voivodship_to_protocole[unit_id]

    def get_candidate(self, unit_id):
        okreg_ids = self.get_okreg(unit_id)
        candidates_ids = []
        for okreg_id in okreg_ids:
            candidates_ids += self._okreg_to_candidate[okreg_id]
        return candidates_ids

    def get_list(self, unit_id):
        okreg_ids = self.get_okreg(unit_id)
        list_ids = []
        for okreg_id in okreg_ids:
            list_ids += self._okreg_to_list[okreg_id]
        return list_ids

    def get_mandate(self, unit_id):
        okreg_ids = self.get_okreg(unit_id)
        mandate_ids = []
        for okreg_id in okreg_ids:
            mandate_ids += self._okreg_to_mandate[okreg_id]
        return mandate_ids

    def get_wyniki(self, unit_id):
        wyniki_dict = {}
        okregi_ids = self.get_okreg(unit_id)
        for okreg_id in okregi_ids:
            table_name_i = self._wyniki_table_names[okreg_id]
            wyniki_dict[table_name_i] = []

        obwody_ids = self.get_obwod(unit_id)
        for obwod_id in obwody_ids:
            wyniki_id = self._obwod_to_wyniki[obwod_id]
            table_name_i = self._obwod_to_table_name[obwod_id]
            wyniki_dict[table_name_i].append(wyniki_id)

        return wyniki_dict
