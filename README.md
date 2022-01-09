# pkwscraper
Scraping, processing and visualizing election results in Poland.

***

**Project website:** https://github.com/msmiglo/pkwscraper  

Wiki page: https://github.com/msmiglo/pkwscraper/wiki  
Tasks list: https://github.com/msmiglo/pkwscraper/issues  
Requirements analysis: https://github.com/msmiglo/pkwscraper/wiki#requirements  

**Example visualizations:**  
[in preparation]

***

This project uses no third-party DB engine. I've created simple wrapper to simulate NoSQL DB engine by wrapping csv files reader/writer. Tables are stored in the csv file each. The query syntax and API is inspired by MongoDB. This is to learn and thereafter show my deeper understaning of DataBase underlying logic and performance-related challenges (not that these challenges were solved here 😉, they were only encountered).

Project is split into 3 parts:
- downloading/scraping raw data from PKW ("Państwowa Komisja Wyborcza") website,
- processing them to obtain useful and easily accessible database,
- visualizing desired results of elections on map of Poland.

It also includes API for writing custom scripts. That will allow users to visualize other direct results or some self-defined complex expresions on results values.
