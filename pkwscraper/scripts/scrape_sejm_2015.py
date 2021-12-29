from pkwscraper.lib.scraper.sejm_2015_scraper import Sejm2015Scraper


def main():
    scraper = Sejm2015Scraper()
    scraper.run_all()


if __name__ == "__main__":
    main()
