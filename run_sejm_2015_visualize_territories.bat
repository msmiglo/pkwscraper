@echo off
:: run the script to scrape sejm 2015 elections results
python -m pkwscraper.lib.visualizing.visualize

:: pause the script to inspect the results
echo Finished.
pause
