
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
    ".zip",
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
        # convert url to file path
        if not relative_url.startswith("/"):
            raise ValueError('Relative URL path should start with "/".')
        filename = self._convert_filename(relative_url)
        filepath = os.path.join(self.__local_directory, filename)

        # check cache
        if not force and os.path.exists(filepath):
            file_content = self._load_file(filepath)
            return file_content

        # download file from Internet
        url = self.__base_url + relative_url
        response = requests.get(url)
        if response.status_code != 200:
            raise ConnectionError(
                f'Server did not return a requested resource. '
                f'Reason: "{response.reason}".')

        # cache and return the file content
        file_content = response.content
        self._save_file(file_content, filepath)
        return file_content

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
        with open(filepath, "wb") as f:
            f.write(content)

    @staticmethod
    def _load_file(filepath):
        with open(filepath, "rb") as f:
            content = f.read()
        return content
