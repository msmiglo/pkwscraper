# `pkwscraper` project
Scraping, processing and visualizing election results in Poland.

***

## Summary:

This project is related to Data Science (specifically: data engineering). The data collected here come from different sources - csv, xls and xlsx files, html pages or blobs from databases. Almost each table of raw data had some kind of exceptions of any kind - from surplus spaces, throug differing names of communes ("gminy"), wrongly supported city-districts (but only in Łódź and Kraków), ending on 5 polling districts located on ships on Baltic Sea. Scraping and plotting geographical shapes of administration units was also challenging - it needed proper scaling to match specific location on map of whole country and also some knowledge of topology to take into account holes in some districts shape. The problems with custom DB-engine performance (long time of loading the largest table and operating on it) lead ultimately to rewrite it from pure python to C++ dynamic linked library (DLL). The design of software implements the SOLID principles and is extensible for different elections in Poland, which may be of great significance right after the publication of results of future ones, when making some complex plots will be needed fast. The outcome of the project gives the ability to freely design, visualize and analize different measures of voting results. It gives a powerful tool to anybody involved in politics in Poland, as well as casual entertainment.

***

**Project website:** https://github.com/msmiglo/pkwscraper  

Wiki page: https://github.com/msmiglo/pkwscraper/wiki  
Tasks list: https://github.com/msmiglo/pkwscraper/issues  
Requirements analysis: https://github.com/msmiglo/pkwscraper/wiki#requirements  

**Example visualizations:**  
[in preparation]

***

**Data management:**

This project uses no third-party DB engine. I've created simple wrapper to simulate NoSQL DB engine by wrapping csv files reader/writer. Tables are stored in the csv file each. The query syntax and API is inspired by MongoDB. This is to learn and thereafter show my deeper understaning of DataBase underlying logic and performance-related challenges (not that these challenges were solved here 😉, they were only encountered).

***

**Project structure:**

Project is split into 3 parts:
- downloading/scraping raw data from PKW ("Państwowa Komisja Wyborcza") website,
- processing them to obtain useful and easily accessible database,
- visualizing desired results of elections on map of Poland.

***

**API**:

The project includes API for writing custom scripts. That will allow users to visualize other direct results or some self-defined complex expresions on results values. Necessary documentation can be found in repository.

Database structure for preprocessed data: https://github.com/msmiglo/pkwscraper/blob/master/pkwscraper/doc/data_architecture.txt
DB usage: [`DbDriver` interface](https://github.com/msmiglo/pkwscraper/blob/master/pkwscraper/lib/dbdriver.py#L243), [`Table` interface](https://github.com/msmiglo/pkwscraper/blob/master/pkwscraper/lib/dbdriver.py#L12)
