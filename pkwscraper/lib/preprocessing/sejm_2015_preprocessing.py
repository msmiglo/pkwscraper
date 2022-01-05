
'''import re
from zipfile import ZipFile

from lxml import html
from openpyxl import load_workbook
import xlrd'''

from pkwscraper.lib.dbdriver import DbDriver
#from pkwscraper.lib.downloader import Downloader
from pkwscraper.lib.scraper.base_preprocessing import BasePreprocessing


ELECTION_TYPE = "sejm"
YEAR = 2015
RAW_DATA_DIRECTORY = "./pkwscraper/data/raw/sejm/2015/"
RESCRIBED_DATA_DIRECTORY = "./pkwscraper/data/rescribed/sejm/2015/"
PREPROCESSED_DATA_DIRECTORY = "./pkwscraper/data/preprocessed/sejm/2015/"


class Sejm2015Preprocessing(BasePreprocessing):
    def __init__(self):
        print("opening DB...")
        # open source DB read only
        #self.source_db = DbDriver(RESCRIBED_DATA_DIRECTORY, read_only=True)
        # open target DB
        #self.target_db = DbDriver(PREPROCESSED_DATA_DIRECTORY)
        print("DB opened.")

    def run_all(self):
        #self._preprocess_xxx()

        print("dumping DB tables...")
        #self.target_db.dump_tables()
        print("DB closed.")
        print()
