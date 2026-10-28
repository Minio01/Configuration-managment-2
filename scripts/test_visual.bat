@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

set CONFIGS=scripts\examples\requests.xml scripts\examples\flask.xml
set CONFIGS=%CONFIGS% scripts\examples\pandas.xml
set CONFIGS=%CONFIGS% scripts\graphs\diamond.xml scripts\graphs\complex_cycle.xml

for %%f in (%CONFIGS%) do (
    echo === %%f ===
    echo ^> py src\main.py %%f
    py src\main.py %%f
    echo.
)
