
from pkwscraper.lib.preprocessing.sejm_2015_preprocessing import \
     Sejm2015Preprocessing


def main():
    preprocessing = Sejm2015Preprocessing()
    preprocessing.run_all()


if __name__ == "__main__":
    main()
