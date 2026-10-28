@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo === Корректная конфигурация (PyPI) ===
echo ^> py src\main.py config.xml
py src\main.py config.xml
echo.
echo === Корректная конфигурация (тестовый репозиторий) ===
echo ^> py src\main.py config_test.xml
py src\main.py config_test.xml
echo.
echo === Файл конфигурации не существует ===
echo ^> py src\main.py no_such_config.xml
py src\main.py no_such_config.xml
echo.
for %%f in (scripts\errors\*.xml) do (
    echo === %%~nf ===
    echo ^> py src\main.py %%f
    py src\main.py %%f
    echo.
)
