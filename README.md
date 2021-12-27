# pkwscraper
Scraping, processing and visualizing election results in Poland.

This project uses no third-party DB engine. I've created simple wrapper to simulate NoSQL DB engine by wrapping csv files reader/writer. Tables are stored in the csv file each. The query syntax and API is inspired by MongoDB. This is to learn and thereafter show my deeper understaning of DataBase underlying logic and performance-related challenges.

Project is split into 3 parts:
- downloading raw data from PKW website,
- processing them to obtain useful and easily accessible database,
- visualizing desired results of elections on map of Poland.

It also includes API for writing custom scripts. That will allow users to visualize other direct results or some self-defined complex expresions on results values.
