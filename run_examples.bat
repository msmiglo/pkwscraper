@echo off
:: enable setting variable in each repetition of loop
SETLOCAL EnableDelayedExpansion

:: iterate over example python scripts
FOR %%f IN (.\pkwscraper\examples\*.py) DO (
  SET module_name=%%~nf
  echo running '!module_name!' example...
  python -m pkwscraper.examples.!module_name!
  echo.
)

:: pause the script to inspect the results
echo Finished.
pause
