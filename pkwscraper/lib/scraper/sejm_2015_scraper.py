
from pkwscraper.lib.dbdriver import DbDriver
from pkwscraper.lib.downloader import Downloader
from pkwscraper.lib.scraper.base_scraper import BaseScraper


ELECTION_TYPE = "sejm"
YEAR = 2015
RAW_DATA_DIRECTORY = "./pkwscraper/data/raw/sejm/2015/"
RESCRIBED_DATA_DIRECTORY = "./pkwscraper/data/rescribed/sejm/2015/"
PREPROCESSED_DATA_DIRECTORY = "./pkwscraper/data/preprocessed/sejm/2015/"


class Sejm2015Scraper(BaseScraper):
    def __init__(self):
        # create downloader object
        self.dl = Downloader(year=2015, directory=RAW_DATA_DIRECTORY)
        # open db for rescribing
        self.db = DbDriver(RESCRIBED_DATA_DIRECTORY)

    def _download_voivodships(self):
        pass

    def _download_okregi(self):
        pass

    def _download_committees(self):
        pass

    def _download_candidates(self):
        pass

    def _download_mandates_winners(self):
        pass

    def _download_powiaty(self):
        pass

    def _download_gminy(self):
        pass

    def _download_obwody(self):
        pass

    def _download_voting_results(self):
        pass

    def _rescribe_to_raw_db(self):
        pass

    def run_all(self):
        self._download_voivodships()
        self._download_okregi()
        self._download_committees()
        self._download_candidates()
        self._download_mandates_winners()
        self._download_powiaty()
        self._download_gminy()
        self._download_obwody()
        self._download_voting_results()
        it = True
        needed = False
        if it is needed:
            self._rescribe_to_raw_db()
