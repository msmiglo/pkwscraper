
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

from pkwscraper.lib.elections import Elections
from pkwscraper.lib.preprocessing.sejm_2015_preprocessing \
    import Sejm2015Preprocessing
from pkwscraper.lib.scraper.sejm_2015_scraper import (
    Sejm2015Scraper,
    RAW_DATA_DIRECTORY,
    RESCRIBED_DATA_DIRECTORY,
    PREPROCESSED_DATA_DIRECTORY
)


class TestElections(TestCase):
    """
    - test wrong elections type
    - test wrong elections year
    - test not implemented elections
    - test wrong elections
    - test init
    - test directories
    - test base url path
    - test election type
    - test year
    - test get scraper class
    - test get preprocessing class
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_wrong_elections_type(self):
        with self.assertRaises(ValueError):
            Elections("Rada Polityki Pieniężnej", 2015)

    def test_wrong_elections_year(self):
        with self.assertRaises(ValueError):
            Elections("sejm", "mcmlxxv")

    def test_not_implemented_elections(self):
        with self.assertRaises(NotImplementedError):
            Elections("sejm", 2019)
        with self.assertRaises(NotImplementedError):
            Elections("sejm", "2023")

    def test_wrong_elections(self):
        with self.assertRaises(ValueError):
            Elections("sejm", 2017)

    def test_init(self):
        ele = Elections("Sejm", "2015")
        # check if correctly set
        self.assertEqual(ele._Elections__elections_type, "sejm")
        self.assertEqual(ele._Elections__elections_year, 2015)
        # check if set at all
        ele._Elections__base_url
        ele._Elections__raw_dir
        ele._Elections__rescribed_dir
        ele._Elections__preprocessed_dir
        ele._Elections__visualized_dir
        ele._Elections__ScraperClass
        ele._Elections__PreprocessingClass

    def test_directories(self):
        ele = Elections("Sejm", "2015")
        raw_dir = ele.raw_dir
        rescribed_dir = ele.rescribed_dir
        preprocessed_dir = ele.preprocessed_dir
        visualized_dir = ele.visualized_dir
        self.assertEqual(raw_dir, RAW_DATA_DIRECTORY)
        self.assertEqual(rescribed_dir, RESCRIBED_DATA_DIRECTORY)
        self.assertEqual(preprocessed_dir, PREPROCESSED_DATA_DIRECTORY)
        self.assertEqual(
            visualized_dir, "./pkwscraper/data/sejm/2015/visualized/")

    def test_base_url_path(self):
        ele = Elections("Sejm", "2015")
        base_url = ele.base_url
        self.assertEqual(base_url, "https://parlament2015.pkw.gov.pl")

    def test_election_type(self):
        ele = Elections("Sejm", "2015")
        election_type = ele.election_type
        self.assertEqual(election_type, "sejm")

    def test_year(self):
        ele = Elections("Sejm", "2015")
        year = ele.year
        self.assertEqual(year, 2015)

    def test_get_scraper_class(self):
        ele = Elections("Sejm", "2015")
        _ScraperClass = ele.get_scraper_class()
        self.assertIs(_ScraperClass, Sejm2015Scraper)

    def test_get_preprocessing_class(self):
        ele = Elections("Sejm", "2015")
        _PreprocessingClass = ele.get_preprocessing_class()
        self.assertIs(_PreprocessingClass, Sejm2015Preprocessing)


if __name__ == "__main__":
    main()
