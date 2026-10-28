@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

for %%f in (scripts\graphs\*.xml) do (
    echo === %%~nf ===
    echo ^> py src\main.py %%f
    py src\main.py %%f
    echo.
)
