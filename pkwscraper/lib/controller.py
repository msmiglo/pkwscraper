
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


class DbReferences:
    @staticmethod
    def inverse_dict(dictionary):
        # TODO
        pass

    def __init__(self, db, granularity=None):
        # TODO - GRANULARITY
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

        # direct indexes
        self._voivodships = db["województwa"].find({}, fields="_id")
        self._wyniki_table_names = {
            okreg_id: f"wyniki_{okreg_no}"
            for okreg_id, okreg_no
            in db["okręgi"].find({}, fields=["_id", "number"])
        }

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

        self._powiat_to_okreg = {
            powiat_id: [okreg_id]
            for okreg_id, powiat_list in self._okreg_to_powiat.items()
            for powiat_id in powiat_list
        }

        self._gmina_to_okreg = {}
        for gmina_id in self._gmina_to_powiat.keys():
            powiat_id = self._gmina_to_powiat[gmina_id][0]
            okreg_id = self._powiat_to_okreg[powiat_id][0]
            self._gmina_to_okreg[gmina_id] = [okreg_id]

        self._gmina_to_voivodship = {}
        for gmina_id in self._gmina_to_powiat.keys():
            powiat_id = self._gmina_to_powiat[gmina_id][0]
            voivodship_id = self._powiat_to_voivodship[powiat_id][0]
            self._gmina_to_voivodship[gmina_id] = [voivodship_id]

        self._okreg_to_voivodship = {}
        for okreg_id in self._okreg_to_powiat.keys():
            powiat_id = self._okreg_to_powiat[okreg_id][0]
            voivodship_id = self._powiat_to_voivodship[powiat_id][0]
            self._okreg_to_voivodship[okreg_id] = [voivodship_id]

        self._powiat_to_gmina = {
            powiat_id: [] for powiat_id
            in self._powiat_to_voivodship.keys()
        }
        for gmina_id, powiaty in self._gmina_to_powiat.items():
            powiat_id = powiaty[0]
            self._powiat_to_gmina[powiat_id].append(gmina_id)

        self._okreg_to_gmina = {
            okreg_id: [] for okreg_id
            in self._okreg_to_powiat.keys()
        }
        for gmina_id, okregi in self._gmina_to_okreg.items():
            okreg_id = okregi[0]
            self._okreg_to_gmina[okreg_id].append(gmina_id)

        self._voivodship_to_gmina = {
            voivodship_id: [] for voivodship_id
            in self._voivodships
        }
        for gmina_id, voivodship_list in self._gmina_to_voivodship.items():
            voivodship_id = voivodship_list[0]
            self._voivodship_to_gmina[voivodship_id].append(gmina_id)

        self._voivodship_to_powiat = {
            voivodship_id: [] for voivodship_id
            in self._voivodships
        }
        for powiat_id, voivodship_list in self._powiat_to_voivodship.items():
            voivodship_id = voivodship_list[0]
            self._voivodship_to_powiat[voivodship_id].append(powiat_id)

        self._voivodship_to_okreg = {
            voivodship_id: [] for voivodship_id
            in self._voivodships
        }
        for okreg_id, voivodship_list in self._okreg_to_voivodship.items():
            voivodship_id = voivodship_list[0]
            self._voivodship_to_okreg[voivodship_id].append(okreg_id)

        self._gmina_to_obwod = {
            gmina_id: [] for gmina_id in self._gmina_to_powiat.keys()}
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

        obwod_to_protocole = {
            obwod_id: protocole_id
            for protocole_id, obwod_id
            in db["protokoły"].find({}, fields=["_id", "obwod"])
        }

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
        self._okreg_to_candidate = {
            okreg_id: [] for okreg_id in self._okreg_to_voivodship.keys()}
        self._okreg_to_list = {
            okreg_id: [] for okreg_id in self._okreg_to_voivodship.keys()}
        self._okreg_to_mandate = {
            okreg_id: [] for okreg_id in self._okreg_to_voivodship.keys()}

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
        self._obwod_to_wyniki = {}
        for table_name_i in self._wyniki_table_names.values():
            for wyniki_id, obwod_id in db[table_name_i].find(
                    {}, fields=["_id", "obwod"]):
                self._obwod_to_wyniki[obwod_id] = wyniki_id

        print("Indexes for data created.")
        print()

    def gmina_to_powiat(self, gmina_id):
        return self._gmina_to_powiat[gmina_id]

    def gmina_to_okreg(self, gmina_id):
        return self._gmina_to_okreg[gmina_id]

    def gmina_to_voivodship(self, gmina_id):
        return self._gmina_to_voivodship[gmina_id]


    def powiat_to_gmina(self, powiat_id):
        return self._powiat_to_gmina[powiat_id]

    def powiat_to_okreg(self, powiat_id):
        return self._powiat_to_okreg[powiat_id]

    def powiat_to_voivodship(self, powiat_id):
        return self._powiat_to_voivodship[powiat_id]


    def okreg_to_gmina(self, okreg_id):
        return self._okreg_to_gmina[okreg_id]

    def okreg_to_powiat(self, okreg_id):
        return self._okreg_to_powiat[okreg_id]

    def okreg_to_voivodship(self, okreg_id):
        return self._okreg_to_voivodship[okreg_id]


    def voivodship_to_gmina(self, voivodship_id):
        return self._voivodship_to_gmina[voivodship_id]

    def voivodship_to_powiat(self, voivodship_id):
        return self._voivodship_to_powiat[voivodship_id]

    def voivodship_to_okreg(self, voivodship_id):
        return self._voivodship_to_okreg[voivodship_id]


    def gmina_to_obwod(self, gmina_id):
        return self._gmina_to_obwod[gmina_id]

    def gmina_to_protocole(self, gmina_id):
        return self._gmina_to_protocole[gmina_id]

    def gmina_to_candidate(self, gmina_id):
        okreg_id = self._gmina_to_okreg[gmina_id][0]
        return self._okreg_to_candidate[okreg_id]

    def gmina_to_list(self, gmina_id):
        okreg_id = self._gmina_to_okreg[gmina_id][0]
        return self._okreg_to_list[okreg_id]

    def gmina_to_mandate(self, gmina_id):
        okreg_id = self._gmina_to_okreg[gmina_id][0]
        return self._okreg_to_mandate[okreg_id]

    def gmina_to_wyniki(self, gmina_id):
        okreg_id = self._gmina_to_okreg[gmina_id][0]
        table_name_i = self._wyniki_table_names[okreg_id]
        obwody_ids = self._gmina_to_obwod[gmina_id]
        wyniki_ids = [self._obwod_to_wyniki[obwod_id]
                      for obwod_id in obwody_ids]
        return {table_name_i: wyniki_ids}


    def powiat_to_obwod(self, powiat_id):
        return self._powiat_to_obwod[powiat_id]

    def powiat_to_protocole(self, powiat_id):
        return self._powiat_to_protocole[powiat_id]

    def powiat_to_candidate(self, powiat_id):
        okreg_id = self._powiat_to_okreg[powiat_id][0]
        return self._okreg_to_candidate[okreg_id]

    def powiat_to_list(self, powiat_id):
        okreg_id = self._powiat_to_okreg[powiat_id][0]
        return self._okreg_to_list[okreg_id]

    def powiat_to_mandate(self, powiat_id):
        okreg_id = self._powiat_to_okreg[powiat_id][0]
        return self._okreg_to_mandate[okreg_id]

    def powiat_to_wyniki(self, powiat_id):
        okreg_id = self._powiat_to_okreg[powiat_id][0]
        table_name_i = self._wyniki_table_names[okreg_id]
        obwody_ids = self._powiat_to_obwod[powiat_id]
        wyniki_ids = [self._obwod_to_wyniki[obwod_id]
                      for obwod_id in obwody_ids]
        return {table_name_i: wyniki_ids}


    def okreg_to_obwod(self, okreg_id):
        return self._okreg_to_obwod[okreg_id]

    def okreg_to_protocole(self, okreg_id):
        return self._okreg_to_protocole[okreg_id]

    def okreg_to_candidate(self, okreg_id):
        return self._okreg_to_candidate[okreg_id]

    def okreg_to_list(self, okreg_id):
        return self._okreg_to_list[okreg_id]

    def okreg_to_mandate(self, okreg_id):
        return self._okreg_to_mandate[okreg_id]

    def okreg_to_wyniki(self, okreg_id):
        table_name_i = self._wyniki_table_names[okreg_id]
        obwody_ids = self._okreg_to_obwod[okreg_id]
        wyniki_ids = [self._obwod_to_wyniki[obwod_id]
                      for obwod_id in obwody_ids]
        return {table_name_i: wyniki_ids}


    def voivodship_to_obwod(self, voivodship_id):
        return self._voivodship_to_obwod[voivodship_id]

    def voivodship_to_protocole(self, voivodship_id):
        return self._voivodship_to_protocole[voivodship_id]

    def voivodship_to_candidate(self, voivodship_id):
        okreg_ids = self._voivodship_to_okreg[voivodship_id]
        candidates_ids = []
        for okreg_id in okreg_ids:
            candidates_ids += self._okreg_to_candidate[okreg_id]
        return candidates_ids

    def voivodship_to_list(self, voivodship_id):
        okreg_ids = self._voivodship_to_okreg[voivodship_id]
        list_ids = []
        for okreg_id in okreg_ids:
            list_ids += self._okreg_to_list[okreg_id]
        return list_ids

    def voivodship_to_mandate(self, voivodship_id):
        okreg_ids = self._voivodship_to_okreg[voivodship_id]
        mandate_ids = []
        for okreg_id in okreg_ids:
            mandate_ids += self._okreg_to_mandate[okreg_id]
        return mandate_ids

    def voivodship_to_wyniki(self, voivodship_id):
        wyniki_dict = {}
        okregi_ids = self._voivodship_to_okreg[powiat_id]
        for okreg_id in okregi_ids:
            table_name_i = self._wyniki_table_names[okreg_id]
            obwody_ids = self._okreg_to_obwod[powiat_id]
            wyniki_ids = [self._obwod_to_wyniki[obwod_id]
                          for obwod_id in obwody_ids]
            wyniki_dict[table_name_i] = wyniki_ids
        return wyniki_dict


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
        db_refs = DbReferences(self.db)

        # split DB into granularity units
        if self.granularity == "województwa":
            pass

        elif self.granularity == "okręgi":
            pass

        elif self.granularity == "powiaty":
            pass

        elif self.granularity == "gminy":
            # do job
            gminy = self.db[self.granularity].find({})

            for gmina_id, gmina in gminy.items():
                # get IDs of records
                powiat_ids = db_refs.gmina_to_powiat(gmina_id)
                okreg_ids = db_refs.gmina_to_okreg(gmina_id)
                voivodship_ids = db_refs.gmina_to_voivodship(gmina_id)
                obwody_ids = db_refs.gmina_to_obwod(gmina_id)
                protocole_ids = db_refs.gmina_to_protocole(gmina_id)
                list_ids = db_refs.gmina_to_list(gmina_id)
                candidate_ids = db_refs.gmina_to_candidate(gmina_id)
                mandate_ids = db_refs.gmina_to_mandate(gmina_id)
                wyniki_ids = db_refs.gmina_to_wyniki(gmina_id)

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
        vis = Visualizer(
            regions, values, self.colormap, contours=outline_regions,
            interpolation=self.interpolation, title=self.title,
            color_legend=self.show_legend, grid=self.show_grid
        )

        # normalize values if set
        if self.normalization:
            vis.normalize_values()

        # apply colormap to values
        vis.render_colors()

        # prepare plot
        vis.prepare()

        ### TODO # add title, legend, grid, values, etc.

        # render plot to window or file
        if self.output_filename:
            if not os.path.exists(self.visualized_dir):
                os.makedirs(self.visualized_dir)
            output_path = self.visualized_dir + self.output_filename
            vis.save_image(output_path)
        else:
            vis.show()

    def run(self):
        self._load_db()
        self._visualize()

    def show_db_schema(self):
        """ Show tables and fields in DB as user guide. """
        raise NotImplementedError("TODO")
        return {tables: {columns: [values_type / enumerating]}}
        pass
