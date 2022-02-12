
import json
import os

import pkwscraper.lib.elections
import pkwscraper.lib.scraper.sejm_2015_scraper
from pkwscraper.lib.scraper.sejm_2015_scraper import Sejm2015Scraper
from pkwscraper.lib.preprocessing.sejm_2015_preprocessing import \
     Sejm2015Preprocessing
'''from pkwscraper.lib.scraper.sejm_2019_scraper import Sejm2019Scraper
from pkwscraper.lib.scraper.sejm_2023_scraper import Sejm2023Scraper
from pkwscraper.lib.preprocessing.sejm_2019_preprocessing import \
     Sejm2019Preprocessing
from pkwscraper.lib.preprocessing.sejm_2023_preprocessing import \
     Sejm2023Preprocessing'''

from pkwscraper.lib.dbdriver import DbDriver
from pkwscraper.lib.region import Region
from pkwscraper.lib.visualizer import Visualizer

"""
Concepts dictionary explained:

- user function - the function passed to class that takes data for
    single territorial unit and returns a value or vector of values;
- granularity - level of territorial units at which data will be split
    before passing to the function;
- downloading and scraping - first stage of data processing - obtaining
    raw data from internet, it includes rescribing to db tables;
- preprocessing - cleaning rescribed data, making them ready to use
    by visualizing step;
- visualizing - taking preprocessed data and making plots with it;

- For more, look for explanation in `visualizer.py`.
"""


class Controller:
    def __init__(self, elections, function, colormap, granularity,
                outlines_granularity=None, normalization=True,
                 title=None, show_legend=False, show_grid=False,
                 output_filename=None, interpolation='linear'):
        """
        output_file - str or None - if None - the result will be
            displayed in new window
        """
        table_names_dict = {
            "voivodships": "województwa",
            "constituencies": "okręgi",
            "districts": "powiaty",
            "communes": "gminy",
        }
        if granularity in table_names_dict:
            granularity = table_names_dict[granularity]
        if outlines_granularity in table_names_dict:
            outlines_granularity = table_names_dict[outlines_granularity]

        # basic correctness checks
        if granularity not in ["województwa", "okręgi",
                               "powiaty", "gminy"]:
            raise ValueError(
                '`granularity` should be one of: "voivodships", '
                '"constituencies" or "districts", "communes"')

        if outlines_granularity not in ["województwa", "okręgi",
                               "powiaty", "gminy"]:
            raise ValueError(
                '`outlines_granularity` should be one of: "voivodships", '
                '"constituencies" or "districts", "communes"')

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
        self.db = None

        # determine election-specific paths and classes
        # TODO - MOVE TO elections MODULE
        if not isinstance(elections, tuple) or len(elections) != 2:
            raise TypeError("Please, provide elections identifier: (type, year).")
        body, year = elections
        if not body in ["Sejm", "Senat", "Europarlament",
                        "Prezydent", "Samorząd", "Referendum"]:
            raise ValueError('Please specify the election type from: "Sejm", "Senat", "Europarlament", "Prezydent", "Samorząd" or "Referendum".')
        try:
            year = int(year)
        except (TypeError, ValueError):
            raise ValueError("Please, provide elections year.")
        self.elected_body = body
        self.elections_year = year
        # get election specific addresses and directories
        #     directories to: raw/rescribed/preprocessed/visualized
        #     data - that is the images are 4th stage of data
        #     processing
        # TODO - MOVE TO elections MODULE
        if elections == ("Sejm", 2015):
            self._ScraperClass = Sejm2015Scraper  # pkwscraper.lib.elections.get_classes(elections)["scraper"]
            self._PreprocessingClass = Sejm2015Preprocessing  # pkwscraper.lib.elections.get_classes(elections)["preprocessing"]
            self.raw_dir = pkwscraper.lib.scraper.sejm_2015_scraper.RAW_DATA_DIRECTORY
            self.rescribed_dir = pkwscraper.lib.scraper.sejm_2015_scraper.RESCRIBED_DATA_DIRECTORY
            self.preprocessed_dir = pkwscraper.lib.scraper.sejm_2015_scraper.PREPROCESSED_DATA_DIRECTORY
            self.visualized_dir = "./pkwscraper/data/sejm/2015/visualized/"
        else:
            raise ValueError("Cannot find analysis for requested elections")
        # get election specific scraper and preprocessor
        pass

    def _scrape(self):
        scraper = self._ScraperClass()
        scraper.run_all()

    def _preprocess(self):
        preprocessing = self._PreprocessingClass()
        preprocessing.run_all()

    def _load_db(self):
        try:
            # try opening preprocessed db
            DbDriver(self.preprocessed_dir, read_only=True)
        except IOError:
            try:
                # preprocessed db cannot be opened, check if there is rescribed db
                DbDriver(self.rescribed_dir, read_only=True)
            except IOError:
                # rescribed db cannot be opened, run downloading and scraping
                self._scrape()
            # rescribed db present, run preprocessing
            self._preprocess()
        # preprocessed db present, load it
        self.db = DbDriver(self.preprocessed_dir, read_only=True)

    def _split_db(self):
        db_refs = DbReferences(self.db, self.granularity)

        # split DB into granularity units
        if self.granularity == "województwa":
            # do job
            voivodships = self.db[self.granularity].find({})

            for voivodship_id, voivodship in voivodships.items():
                # get IDs of records
                gmina_ids = db_refs.get_gmina(voivodship_id)
                powiat_ids = db_refs.get_powiat(voivodship_id)
                okreg_ids = db_refs.get_okreg(voivodship_id)
                obwody_ids = db_refs.get_obwod(voivodship_id)
                protocole_ids = db_refs.get_protocole(voivodship_id)
                list_ids = db_refs.get_list(voivodship_id)
                candidate_ids = db_refs.get_candidate(voivodship_id)
                mandate_ids = db_refs.get_mandate(voivodship_id)
                wyniki_ids = db_refs.get_wyniki(voivodship_id)

                # create tables
                db = DbDriver.__new__(DbDriver)
                db._DbDriver__read_only = False
                db._DbDriver__tables = {}
                db._DbDriver__dropped_tables = []
                db.create_table("województwa")
                db.create_table("okręgi")
                db.create_table("powiaty")
                db.create_table("gminy")
                db.create_table("obwody")
                db.create_table("protokoły")
                db.create_table("mandaty")
                db.create_table("kandydaci")
                db.create_table("listy")

                # copy
                db["województwa"].put(dict(voivodship), _id=voivodship_id)
                tables_ids_list = [
                    ("gminy", gmina_ids),
                    ("powiaty", powiat_ids),
                    ("okręgi", okreg_ids),
                    ("obwody", obwody_ids),
                    ("protokoły", protocole_ids),
                    ("listy", list_ids),
                    ("kandydaci", candidate_ids),
                    ("mandaty", mandate_ids)
                ]
                for table_name_i, ids_list in tables_ids_list:
                    for _id in ids_list:
                        record = self.db[table_name_i][_id]
                        db[table_name_i].put(dict(record), _id=_id)

                # create and copy results tables
                for wyniki_table_name, ids_list in wyniki_ids.items():
                    db.create_table(wyniki_table_name)
                    for _id in ids_list:
                        record = self.db[wyniki_table_name][_id]
                        db[wyniki_table_name].put(dict(record), _id=_id)

                # freeze db and conclude iteration
                db._DbDriver__read_only = True
                yield db

        elif self.granularity == "okręgi":
            # do job
            okregi = self.db[self.granularity].find({})

            for okreg_id, okreg in okregi.items():
                # get IDs of records
                gmina_ids = db_refs.get_gmina(okreg_id)
                powiat_ids = db_refs.get_powiat(okreg_id)
                voivodship_ids = db_refs.get_voivodship(okreg_id)
                obwody_ids = db_refs.get_obwod(okreg_id)
                protocole_ids = db_refs.get_protocole(okreg_id)
                list_ids = db_refs.get_list(okreg_id)
                candidate_ids = db_refs.get_candidate(okreg_id)
                mandate_ids = db_refs.get_mandate(okreg_id)
                wyniki_ids = db_refs.get_wyniki(okreg_id)

                # create tables
                db = DbDriver.__new__(DbDriver)
                db._DbDriver__read_only = False
                db._DbDriver__tables = {}
                db._DbDriver__dropped_tables = []
                db.create_table("województwa")
                db.create_table("okręgi")
                db.create_table("powiaty")
                db.create_table("gminy")
                db.create_table("obwody")
                db.create_table("protokoły")
                db.create_table("mandaty")
                db.create_table("kandydaci")
                db.create_table("listy")

                # copy
                db["okręgi"].put(dict(okreg), _id=okreg_id)
                tables_ids_list = [
                    ("gminy", gmina_ids),
                    ("powiaty", powiat_ids),
                    ("województwa", voivodship_ids),
                    ("obwody", obwody_ids),
                    ("protokoły", protocole_ids),
                    ("listy", list_ids),
                    ("kandydaci", candidate_ids),
                    ("mandaty", mandate_ids)
                ]
                for table_name_i, ids_list in tables_ids_list:
                    for _id in ids_list:
                        record = self.db[table_name_i][_id]
                        db[table_name_i].put(dict(record), _id=_id)

                # create and copy results tables
                for wyniki_table_name, ids_list in wyniki_ids.items():
                    db.create_table(wyniki_table_name)
                    for _id in ids_list:
                        record = self.db[wyniki_table_name][_id]
                        db[wyniki_table_name].put(dict(record), _id=_id)

                # freeze db and conclude iteration
                db._DbDriver__read_only = True
                yield db

        elif self.granularity == "powiaty":
            # do job
            powiaty = self.db[self.granularity].find({})

            for powiat_id, powiat in powiaty.items():
                # get IDs of records
                gmina_ids = db_refs.get_gmina(powiat_id)
                okreg_ids = db_refs.get_okreg(powiat_id)
                voivodship_ids = db_refs.get_voivodship(powiat_id)
                obwody_ids = db_refs.get_obwod(powiat_id)
                protocole_ids = db_refs.get_protocole(powiat_id)
                list_ids = db_refs.get_list(powiat_id)
                candidate_ids = db_refs.get_candidate(powiat_id)
                mandate_ids = db_refs.get_mandate(powiat_id)
                wyniki_ids = db_refs.get_wyniki(powiat_id)

                # create tables
                db = DbDriver.__new__(DbDriver)
                db._DbDriver__read_only = False
                db._DbDriver__tables = {}
                db._DbDriver__dropped_tables = []
                db.create_table("województwa")
                db.create_table("okręgi")
                db.create_table("powiaty")
                db.create_table("gminy")
                db.create_table("obwody")
                db.create_table("protokoły")
                db.create_table("mandaty")
                db.create_table("kandydaci")
                db.create_table("listy")

                # copy
                db["powiaty"].put(dict(powiat), _id=powiat_id)
                tables_ids_list = [
                    ("gminy", gmina_ids),
                    ("okręgi", okreg_ids),
                    ("województwa", voivodship_ids),
                    ("obwody", obwody_ids),
                    ("protokoły", protocole_ids),
                    ("listy", list_ids),
                    ("kandydaci", candidate_ids),
                    ("mandaty", mandate_ids)
                ]
                for table_name_i, ids_list in tables_ids_list:
                    for _id in ids_list:
                        record = self.db[table_name_i][_id]
                        db[table_name_i].put(dict(record), _id=_id)

                # create and copy results tables
                for wyniki_table_name, ids_list in wyniki_ids.items():
                    db.create_table(wyniki_table_name)
                    for _id in ids_list:
                        record = self.db[wyniki_table_name][_id]
                        db[wyniki_table_name].put(dict(record), _id=_id)

                # freeze db and conclude iteration
                db._DbDriver__read_only = True
                yield db

        elif self.granularity == "gminy":
            # do job
            gminy = self.db[self.granularity].find({})

            for gmina_id, gmina in gminy.items():
                # get IDs of records
                powiat_ids = db_refs.get_powiat(gmina_id)
                okreg_ids = db_refs.get_okreg(gmina_id)
                voivodship_ids = db_refs.get_voivodship(gmina_id)
                obwody_ids = db_refs.get_obwod(gmina_id)
                protocole_ids = db_refs.get_protocole(gmina_id)
                list_ids = db_refs.get_list(gmina_id)
                candidate_ids = db_refs.get_candidate(gmina_id)
                mandate_ids = db_refs.get_mandate(gmina_id)
                wyniki_ids = db_refs.get_wyniki(gmina_id)

                # create tables
                db = DbDriver.__new__(DbDriver)
                db._DbDriver__read_only = False
                db._DbDriver__tables = {}
                db._DbDriver__dropped_tables = []
                db.create_table("województwa")
                db.create_table("okręgi")
                db.create_table("powiaty")
                db.create_table("gminy")
                db.create_table("obwody")
                db.create_table("protokoły")
                db.create_table("mandaty")
                db.create_table("kandydaci")
                db.create_table("listy")

                # copy
                db["gminy"].put(dict(gmina), _id=gmina_id)
                tables_ids_list = [
                    ("powiaty", powiat_ids),
                    ("okręgi", okreg_ids),
                    ("województwa", voivodship_ids),
                    ("obwody", obwody_ids),
                    ("protokoły", protocole_ids),
                    ("listy", list_ids),
                    ("kandydaci", candidate_ids),
                    ("mandaty", mandate_ids)
                ]
                for table_name_i, ids_list in tables_ids_list:
                    for _id in ids_list:
                        record = self.db[table_name_i][_id]
                        db[table_name_i].put(dict(record), _id=_id)

                # create and copy results tables
                for wyniki_table_name, ids_list in wyniki_ids.items():
                    db.create_table(wyniki_table_name)
                    for _id in ids_list:
                        record = self.db[wyniki_table_name][_id]
                        db[wyniki_table_name].put(dict(record), _id=_id)

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
        outline_geos = self.db[self.outlines_granularity].find({}, fields="geo")
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
            if not os.path.exists(self.visualized_dir):
                os.makedirs(self.visualized_dir)
            output_path = self.visualized_dir + self.output_filename
            self.vis.save_image(output_path)
        else:
            self.vis.show()

    def run(self):
        self._load_db()
        self._visualize()

    def show_db_schema(self):
        """ Show tables and fields in DB as user guide. """
        raise NotImplementedError("TODO")
        return {tables: {columns: [values_type / enumerating]}}
        pass


class DbReferences:
    @staticmethod
    def inverse_dict(dictionary):
        values = []
        for value_list in dictionary.values():
            values += value_list

        inversed_dict = {value: [] for value in values}
        for key, value_list in dictionary.items():
            for value in value_list:
                inversed_dict[value].append(key)

        return inversed_dict

    def __init__(self, db, granularity):
        """
        There are needed indexes that assign from:
        voivodships/constituencies/district/communes
        to list of:
        - voivodships
        - constituencies
        - districts
        - communes
        - polling districts
        - protocoles
        they are associated with.

        Alse intermediate assignments are needed from constituencies to:
        - candidates
        - lists
        - mandates

        Results IDs will be dynamically determined.
        """
        print("Creating indexes for data...")

        self.granularity = granularity

        # auxiliary indexes and names lists
        self._voivodships = db["województwa"].find({}, fields="_id")
        self._okregi = db["okręgi"].find({}, fields="_id")
        self._gminy = db["gminy"].find({}, fields="_id")
        self._wyniki_table_names = {
            okreg_id: f"wyniki_{okreg_no}"
            for okreg_id, okreg_no
            in db["okręgi"].find({}, fields=["_id", "number"])
        }
        obwod_to_protocole = {
            obwod_id: protocole_id
            for protocole_id, obwod_id
            in db["protokoły"].find({}, fields=["_id", "obwod"])
        }

        # direct indexes
        self._gmina_to_powiat = {
            gmina_id: [powiat_id]
            for gmina_id, powiat_id
            in db["gminy"].find({}, fields=["_id", "parent"])
        }

        self._powiat_to_voivodship = {
            powiat_id: [voivodship_id]
            for powiat_id, voivodship_id
            in db["powiaty"].find({}, fields=["_id", "parent"])
        }

        self._okreg_to_powiat = {
            okreg_id: json.loads(powiaty)
            for okreg_id, powiaty
            in db["okręgi"].find({}, fields=["_id", "powiat_list"])}

        self._powiat_to_okreg = self.inverse_dict(self._okreg_to_powiat)

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

        self._powiat_to_gmina = self.inverse_dict(self._gmina_to_powiat)

        self._okreg_to_gmina = self.inverse_dict(self._gmina_to_okreg)

        self._voivodship_to_gmina = self.inverse_dict(self._gmina_to_voivodship)

        self._voivodship_to_powiat = self.inverse_dict(
            self._powiat_to_voivodship)

        self._voivodship_to_okreg = self.inverse_dict(self._okreg_to_voivodship)

        self._gmina_to_obwod = {
            gmina_id: [] for gmina_id in self._gminy}
        for obwod_id, gmina_id \
                in db["obwody"].find({}, fields=["_id", "gmina"]):
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
        candidates = db["kandydaci"].find({})  # maybe add `{"is_crossed_out": False}` ?
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

        for mandate_id, candidate_id in db["mandaty"].find(
                {}, fields=["_id", "candidate"]):
            okreg_id = candidates[candidate_id]["constituency"]
            self._okreg_to_mandate[okreg_id].append(mandate_id)

        # results IDs
        self._obwod_to_table_name = {}
        for obwod_id, okreg_id in db["obwody"].find(
                {}, fields=["_id", "constituency"]):
            table_name_i = self._wyniki_table_names[okreg_id]
            self._obwod_to_table_name[obwod_id] = table_name_i

        self._obwod_to_wyniki = {}
        for table_name_i in self._wyniki_table_names.values():
            for wyniki_id, obwod_id in db[table_name_i].find(
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
