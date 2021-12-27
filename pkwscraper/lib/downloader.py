
import os
import requests


BASE_URL_DICT = {
    2011: "https://wybory2011.pkw.gov.pl",
    2015: "https://parlament2015.pkw.gov.pl",
    2019: "https://sejmsenat2019.pkw.gov.pl/sejmsenat2019",
}
ACCEPTED_EXTENSIONS = [
    ".csv",
    ".xls",
    ".xlsx",
    ".htm",
    ".html",
    ".blob",
]


class Downloader:
    def __init__(self, year, directory):
        """
        year: int/str - year of Sejm elections to scrape
        directory: str - local directory for caching files
        """
        # choose base URL for given elections
        self.__base_url = BASE_URL_DICT[int(year)]

        # check if cache directory exists
        if not os.path.isdir(directory):
            raise IOError("The caching directory does not exist!")
        self.__local_directory = directory

    def download(self, relative_url, force=False):
        if not relative_url.startswith("/"):
            raise ValueError('Relative URL path should start with "/".')
        pass

    @staticmethod
    def _convert_filename(relative_url):
        if relative_url == "/":
            relative_url = "/index.html"
        if not any(relative_url.endswith(extension) for extension in ACCEPTED_EXTENSIONS):
            raise ValueError("Unsupported type of requested file.")
        filename = relative_url.replace("/", "_").strip("_")
        return filename

    @staticmethod
    def _save_file(content, filepath):
        pass

    @staticmethod
    def _load_file(filepath):
        pass




'''
=========================
=== RESEARCH NOTES... ===
=========================





exit()

import os

import lxml.html
import pandas as pd
import requests


BASE_URL = "https://parlament2015.pkw.gov.pl"
LOCAL_PATH = "./xlsx_data/"
N_OKREGI = 41


def download_xlsx_data_results(force=False):
    path = "/wyniki_okr_sejm/"

    for i in range(N_OKREGI):
        nr_okregu = "%02i" % (i+1)
        filename = f"{nr_okregu}.xlsx"
        print(filename)

        local_file = LOCAL_PATH + filename
        if os.path.exists(local_file) and not force:
            continue
        url = BASE_URL + path + filename
        resp = requests.get(url)
        print(resp)
        file_content = resp.content
        if resp.status_code == 200:
            with open(local_file, 'wb') as f:
                f.write(file_content)
        else:
            raise ConnectionError


def _extract_region_list(html_content=None):
    # get content
    if html_content is None:
        html_content = open('root.html', 'rb').read()
    root = lxml.html.fromstring(html_content)

    # get table of okregi
    okregi_table_query = '//div[@id="okregi_bottom"]//table'
    okregi_table = root.xpath(okregi_table_query)
    assert len(okregi_table) == 1
    print(okregi_table)
    table_headers = okregi_table[0].xpath('./thead/tr/th/text()')
    table_headers.append('relative_path')
    print(len(table_headers))
    print(table_headers)
    okregi_elems = okregi_table[0].xpath('./tbody/tr')
    print(len(okregi_elems))
    print(okregi_elems)
    okregi = []
    for okreg in okregi_elems:
        # TODO - jeśli jest puste to omija
        okreg_path = okreg.xpath('(./td/a/@href)[1]')
        okreg_list = okreg.xpath('./td/a/text()')
        okreg_list = [el.strip() for el in okreg_list]
        #print(okreg_path)
        #print(okreg_list)
        okregi.append(okreg_list + okreg_path)
    okregi_df = pd.DataFrame(okregi, columns=table_headers)
    okregi_df = okregi_df.set_index("Nr")
    print(okregi_df)
    print(okregi_df.iloc[5])




    
def download_commitees_data(force=False):
    filename = "komitety.csv"
    local_file = LOCAL_PATH + filename
    
    if os.path.exists(local_file) and not force:
        return

    path = "/komitety"
    url = BASE_URL + path
    resp = requests.get(url)
    print(resp)
    html_content = resp.content
##    if resp.status_code == 200:
##        with open('root.html', 'wb') as f:
##            f.write(html_content)
    komitety_df = _extract_commities_list(html_content)
    komitety_df.to_csv(local_file, sep=";")


def check_other_data():
    for filename in [
        '2015-gl-lis-gm.xls',
        '2015-gl-lis-obw.xls',
        '2015-gl-lis-okr.xls',
        '2015-gl-lis-pow.xls',
        '2015-gl-lis-woj.xls',
        'kandsejm2015-10-19-10-00.xls',
        #'kandsen2015-10-19-10-00.xls',
    ]:
        local_file = LOCAL_PATH + filename
        if not os.path.exists(local_file):
            print(
                f'File "{local_file}" not found - download it from PKW site.')
'''
