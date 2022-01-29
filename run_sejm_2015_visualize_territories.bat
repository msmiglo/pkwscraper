@echo off
:: run the script to scrape sejm 2015 elections results
python -m pkwscraper.scripts.visualize_sejm_2015_territories

:: pause the script to inspect the results
echo Finished.
pause
