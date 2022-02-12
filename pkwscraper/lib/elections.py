
from pkwscraper.lib.downloader import BASE_URL_DICT

#import pkwscraper.lib.preprocessing.sejm_2011_preprocessing \
#    as sejm_2015_preprocessing
import pkwscraper.lib.preprocessing.sejm_2015_preprocessing \
    as sejm_2015_preprocessing
#import pkwscraper.lib.preprocessing.sejm_2019_preprocessing \
#    as sejm_2019_preprocessing
#import pkwscraper.lib.preprocessing.sejm_2023_preprocessing \
#    as sejm_2023_preprocessing

#import pkwscraper.lib.scraper.sejm_2011_scraper \
#    as sejm_2015_scraper
import pkwscraper.lib.scraper.sejm_2015_scraper \
    as sejm_2015_scraper
#import pkwscraper.lib.scraper.sejm_2019_scraper \
#    as sejm_2019_scraper
#import pkwscraper.lib.scraper.sejm_2023_scraper \
#    as sejm_2023_scraper


class Elections:
    """ This class uses the Strategy design pattern. """
    def __init__(self, elections_type, year):
        # check correctness
        elections_type = elections_type.lower()
        if not elections_type in [
            "sejm", "senat", "europarlament",
            "prezydent", "samorząd", "referendum"
        ]:
            raise ValueError(
                'Please specify the elections type from: "sejm", "senat",'
                ' "europarlament", "prezydent", "samorząd" or "referendum".')
        try:
            year = int(year)
        except (TypeError, ValueError):
            raise ValueError("Please, provide elections year.")

        # assign values
        self.__elections_type = elections_type
        self.__elections_year = year

        # determine directories, paths and concrete strategy classes
        elections = (elections_type, year)

        if elections == ("sejm", 2011):
            raise NotImplementedError("To be implemented soon.")

        elif elections == ("sejm", 2015):
            self.__base_url = BASE_URL_DICT[2015]
            self.__raw_dir = sejm_2015_scraper.RAW_DATA_DIRECTORY
            self.__rescribed_dir = sejm_2015_scraper.RESCRIBED_DATA_DIRECTORY
            self.__preprocessed_dir = \
                sejm_2015_scraper.PREPROCESSED_DATA_DIRECTORY
            self.__visualized_dir = "./pkwscraper/data/sejm/2015/visualized/"
            self.__ScraperClass = sejm_2015_scraper.Sejm2015Scraper
            self.__PreprocessingClass = \
                sejm_2015_preprocessing.Sejm2015Preprocessing

        elif elections == ("sejm", 2019):
            raise NotImplementedError("To be implemented soon.")

        elif elections == ("sejm", 2023):
            raise NotImplementedError("To be implemented soon.")

        else:
            raise ValueError("Cannot find analysis for requested elections.")

    @property
    def raw_dir(self):
        return str(self.__raw_dir)

    @property
    def rescribed_dir(self):
        return str(self.__rescribed_dir)

    @property
    def preprocessed_dir(self):
        return str(self.__preprocessed_dir)

    @property
    def visualized_dir(self):
        return str(self.__visualized_dir)

    @property
    def base_url(self):
        return str(self.__base_url)

    @property
    def election_type(self):
        return str(self.__elections_type)

    @property
    def year(self):
        return int(self.__elections_year)

    def get_scraper_class(self):
        return self.__ScraperClass

    def get_preprocessing_class(self):
        return self.__PreprocessingClass
