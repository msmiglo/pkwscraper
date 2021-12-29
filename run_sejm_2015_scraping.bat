@echo off
:: run the script to scrape sejm 2015 elections results
python -m pkwscraper.scripts.scrape_sejm_2015

:: pause the script to inspect the results
echo Finished.
pause
