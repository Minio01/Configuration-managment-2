@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

for %%f in (config.xml scripts\examples\*.xml) do (
    echo === %%f ===
    echo ^> py src\main.py %%f
    py src\main.py %%f
    echo.
)
