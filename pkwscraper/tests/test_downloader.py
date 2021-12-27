
import os
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

from pkwscraper.lib.downloader import Downloader


class TestDownloader(TestCase):
    """
    - test init
    - test wrong year of elections
    - test not existing directory
    - test convert filename
    - test check file extension
    - test return cached file
    - test wrong relative path
    - test download and save file
    - test connection error
    - test force redownloading
    """
    def setUp(self):
        self.local_directory = "/raw_data/db"
        self.mock_url_dict = {
            2015: "https://www.pkw2015.pl",
            2019: "https://www.pkw2019.pl",
        }
        self.relative_url = "/0/sejm/15.blob"
        self.filename = "0_sejm_15.blob"
        self.filepath = os.path.join("/raw_data/db", self.filename)
        self.blob_content = b"!@#$%^&*()qwertyuiop"

    def tearDown(self):
        pass

    def test_wrong_year_of_elections(self):
        with patch("pkwscraper.lib.downloader.BASE_URL_DICT",
                   self.mock_url_dict):
            with self.assertRaises(ValueError):
                Downloader("dwa tysiące piętnaście", self.local_directory)
            with self.assertRaises(KeyError):
                Downloader(2017, self.local_directory)

    def test_not_existing_directory(self):
        # arrange
        mock_os = MagicMock()
        mock_os.path.isdir.return_value = False
        local_directory = "/nonexisting/db"
        # act
        with patch("pkwscraper.lib.downloader.os", mock_os):
            with self.assertRaises(IOError):
                Downloader(2015, local_directory)
        # assert
        mock_os.path.isdir.assert_called_once_with(local_directory)

    def test_init(self):
        # arrange
        mock_os = MagicMock()
        mock_os.path.isdir.return_value = True
        # act
        with patch("pkwscraper.lib.downloader.os", mock_os):
            with patch("pkwscraper.lib.downloader.BASE_URL_DICT",
                       self.mock_url_dict):
                dl = Downloader(2015, self.local_directory)
                # assert
                self.assertEqual(dl._Downloader__base_url,
                                 "https://www.pkw2015.pl")
                self.assertEqual(dl._Downloader__local_directory,
                                 "/raw_data/db")

    def test_convert_filename(self):
        # arrange
        rel_url_1 = "/0/wyniki.bmp"
        rel_url_2 = "/0/wyniki.xls"
        rel_url_3 = "/"
        expected_filename_2 = "0_wyniki.xls"
        expected_filename_3 = "index.html"
        
        # act
        with self.assertRaises(ValueError):
            Downloader._convert_filename(rel_url_1)
        result_2 = Downloader._convert_filename(rel_url_2)
        result_3 = Downloader._convert_filename(rel_url_3)

        # assert
        self.assertEqual(result_2, expected_filename_2)
        self.assertEqual(result_3, expected_filename_3)

    def test_check_file_extension(self):
        base = "/0/wyniki."
        bad_extensions = ["doc", "py", "txt", "dat"]
        good_extensions = ["csv", "xls", "xlsx", "htm", "html", "blob"]

        for extension in bad_extensions:
            rel_url = base + extension
            with self.assertRaises(ValueError):
                Downloader._convert_filename(rel_url)

        for extension in good_extensions:
            rel_url = base + extension
            Downloader._convert_filename(rel_url)

    def test_return_cached_file(self):
        # arrange
        dl = MagicMock()
        dl._convert_filename.return_value = self.filepath
        dl._load_file.return_value = self.blob_content
        mock_os = MagicMock()
        mock_os.path.exists.return_value = True

        # act
        with patch("pkwscraper.lib.downloader.os", mock_os):
            file_content = Downloader.download(dl, self.relative_url)

        # assert
        dl._convert_filename.assert_called_once_with(self.relative_url)
        mock_os.path.exists.assert_called_once_with(self.filepath)
        dl._load_file.assert_called_once_with(self.filepath)

    def test_wrong_relative_path(self):
        rel_url = "0/wyniki.csv"
        dl = MagicMock()

        with self.assertRaises(ValueError):
            Downloader.download(dl, rel_url)
        with self.assertRaises(ValueError):
            Downloader.download(dl, rel_url, force=True)

    # TODO - the 3 test below have common fixture - can be shared somehow...
    def test_download_and_save_file(self):
        # arrange
        dl = MagicMock()
        dl._convert_filename.return_value = self.filename
        dl._DbDriver__base_url = self.mock_url_dict[2015]
        dl._DbDriver__local_directory = self.local_directory

        mock_os = MagicMock()
        mock_os.path.exists.return_value = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = self.blob_content

        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        # act
        with patch("pkwscraper.lib.downloader.os", mock_os):
            with patch("pkwscraper.lib.downloader.requests", mock_requests):
                file_content = Downloader.download(dl, self.relative_url)

        # assert
        dl._convert_filename.assert_called_once_with(self.relative_url)
        mock_os.path.exists.assert_called_once_with(self.filepath)
        mock_requests.get.assert_called_once_with(
            self.mock_url_dict[2015]+self.relative_url)
        dl._save_file.assert_called_once_with(self.blob_content, self.filepath)
        self.assertEqual(file_content, self.blob_content)

    def test_connection_error(self):
        # arrange
        dl = MagicMock()
        dl._convert_filename.return_value = self.filename
        dl._DbDriver__base_url = self.mock_url_dict[2015]
        dl._DbDriver__local_directory = self.local_directory

        mock_os = MagicMock()
        mock_os.path.exists.return_value = False

        mock_response = MagicMock()
        mock_response.status_code = 503

        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        # act
        with patch("pkwscraper.lib.downloader.os", mock_os):
            with patch("pkwscraper.lib.downloader.requests", mock_requests):
                with self.assertRaises(ConnectionError):
                    Downloader.download(dl, self.relative_url)

        # assert
        dl._save_file.assert_not_called()

    def test_force_redownloading(self):
        # arrange
        dl = MagicMock()
        dl._convert_filename.return_value = self.filename
        dl._DbDriver__base_url = self.mock_url_dict[2015]
        dl._DbDriver__local_directory = self.local_directory

        mock_os = MagicMock()
        mock_os.path.exists.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = self.blob_content

        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_response

        # act
        with patch("pkwscraper.lib.downloader.os", mock_os):
            with patch("pkwscraper.lib.downloader.requests", mock_requests):
                file_content = Downloader.download(
                    dl, self.relative_url, force=True)

        # assert
        mock_requests.get.assert_called_once_with(
            self.mock_url_dict[2015]+self.relative_url)
        dl._save_file.assert_called_once_with(self.blob_content, self.filepath)
        self.assertEqual(file_content, self.blob_content)

        mock_os.path.exists.assert_not_called()
        dl._load_file.assert_not_called()


if __name__ == "__main__":
    main()
