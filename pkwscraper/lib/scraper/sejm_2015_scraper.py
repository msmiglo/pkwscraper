
from lxml import html
import re

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

    def run_all(self):
        # TODO - check, if the data is already downloaded
        #        and omit unnecessary steps
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
        self.db.dump_tables()
        print()

    def _download_voivodships(self):
        relative_path = "/index.html"
        html_content = self.dl.download(relative_path)
        html_tree = html.fromstring(html_content)

        xpath_voivodships = '/html/body//div[@id="home"]//' \
                            'div[@class="home_content home_mapa"]//svg//a'
        voivodship_elems = html_tree.xpath(xpath_voivodships)
        print()
        print(len(voivodship_elems))

        self.db.create_table("województwa")

        for html_elem in voivodship_elems:
            href_path = html_elem.attrib['xlink:href']
            code = re.findall('\d+', href_path)[0]
            name = html_elem.getchildren()[0].attrib["rel"]
            geo = html_elem.getchildren()[0].attrib["d"]

            self.db["województwa"].put({
                "code": code,
                "name": name,
                "geo": geo
            })

            print(name, end=", ")
        print()

    def _download_okregi(self):
        relative_path = "/349_Wyniki_Sejm/0/0.html"
        html_content = self.dl.download(relative_path)
        html_tree = html.fromstring(html_content)

        xpath_okregi_mapa = '/html/body//div[@id="wyniki1"]//' \
                            'div[@id="wyniki1_top_mapa"]//svg//a'
        okregi_hrefs = html_tree.xpath(xpath_okregi_mapa)
        print()
        print(len(okregi_hrefs))

        xpath_okregi_table = '/html/body//div[@id="wyniki1"]//' \
                             'div[@id="wyniki1_tabela_suma"]//table/tbody/tr'
        okregi_table_rows = html_tree.xpath(xpath_okregi_table)
        print()
        print(len(okregi_table_rows))

        self.db.create_table("okręgi")

        for html_map_elem, html_table_row_elem in \
                zip(okregi_hrefs, okregi_table_rows):
            href_path = html_map_elem.attrib['xlink:href']
            path_elem = html_map_elem.getchildren()[0]
            name = path_elem.attrib["rel"]
            number = re.findall('\d+', name)[0]
            geo = path_elem.attrib["d"]

            cell_elems = html_table_row_elem.getchildren()
            number_elem = cell_elems[0].getchildren()[0]
            href_path_2 = number_elem.attrib['href']
            number_2 = number_elem.text

            voivodship = cell_elems[1].getchildren()[0].text
            headquarters = cell_elems[2].getchildren()[0].text
            mandates = cell_elems[3].getchildren()[0].text

            assert href_path == href_path_2, f"invalid href: {href_path}, {href_path_2}"
            assert number == number_2, f"invalid number: {number}, {number_2}"

            self.db["okręgi"].put({
                "number": number,
                "headquarters": headquarters,
                "voivodship": voivodship,
                "mandates": mandates,
                "geo": geo
            })

            print(name, end=", ")
        print()

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
