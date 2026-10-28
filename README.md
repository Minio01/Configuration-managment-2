# Визуализатор графа зависимостей pip-пакетов

CLI-приложение на Python для анализа зависимостей пакетов Python (pip).
Готовые менеджеры пакетов и библиотеки для получения зависимостей не
используются, только стандартная библиотека Python.

Текущий этап: **1 — минимальный прототип с конфигурацией**. Приложение
читает параметры из XML-файла, проверяет их и выводит в формате
`ключ=значение`.

## Требования

- Python 3.10+
- Windows (`run.bat`) или любая ОС с прямым вызовом `python src/main.py`

## Структура

```
src/main.py        точка входа CLI
src/config.py      чтение и проверка XML-конфигурации
tests/             модульные тесты (unittest)
repos/             тестовые репозитории
scripts/errors/    конфигурации с ошибками для демонстрации
config.xml         пример конфигурации для PyPI
config_test.xml    пример конфигурации для тестового репозитория
run.bat            запуск приложения и тестов
```

## Настройки

Конфигурация задаётся XML-файлом с корневым элементом `<config>`:

```xml
<config>
    <package>requests</package>
    <repository>https://pypi.org/pypi</repository>
    <test_mode>false</test_mode>
    <output_image>graph.svg</output_image>
    <ascii_tree>true</ascii_tree>
    <filter_substring></filter_substring>
</config>
```

| Параметр | Обязателен | Описание |
|---|---|---|
| `package` | да | Имя анализируемого пакета. В тестовом режиме — большие латинские буквы (`A`, `BC`). |
| `repository` | да | URL репозитория (`http`/`https`) или путь к файлу тестового репозитория. Относительный путь считается от каталога конфигурации. |
| `test_mode` | да | Режим работы с тестовым репозиторием: `true`/`false` (`yes`/`no`, `1`/`0`). |
| `output_image` | да | Имя файла с изображением графа, расширение `.svg`, каталог должен существовать. |
| `ascii_tree` | нет | Вывод зависимостей в виде ASCII-дерева: `true`/`false`, по умолчанию `false`. |
| `filter_substring` | нет | Пакеты, имя которых содержит эту подстроку, не учитываются. По умолчанию пусто. |

### Обработка ошибок

При ошибке выводится сообщение `Ошибка конфигурации: ...` в stderr, код
завершения `2`. Проверяются:

- файл не существует, некорректный XML, неверный корневой элемент;
- неизвестный, повторяющийся или вложенный параметр;
- отсутствие или пустое значение обязательного параметра;
- недопустимое имя пакета (в обычном и тестовом режиме);
- URL не `http`/`https`, файл тестового репозитория не найден;
- логические параметры не `true`/`false`;
- файл изображения не `.svg` или его каталог не существует.

Примеры для каждого случая лежат в `scripts/errors/`.

## Функции

`src/config.py`:

- `load_config(path)` — прочитать файл и вернуть объект `Config`;
- `parse_xml(path)` — разобрать XML, проверить корневой элемент;
- `read_values(root)` — собрать значения, проверить обязательные параметры;
- `parse_bool(text, name)` — преобразовать строку в `bool`;
- `check_package(name, test_mode)` — проверить имя пакета;
- `check_repository(value, test_mode, base_dir)` — проверить URL или путь;
- `check_output_image(value, base_dir)` — проверить имя файла изображения;
- `Config.items()` — параметры в виде пар ключ-значение.

`src/main.py`:

- `parse_args(argv)` — аргументы командной строки;
- `format_value(value)` — форматирование значения для вывода;
- `main(argv)` — запуск приложения, возвращает код завершения.

## Сборка и запуск

Сборка не требуется.

```bat
run.bat                     :: запуск с config.xml
run.bat config_test.xml     :: запуск с другой конфигурацией
run.bat test                :: запуск тестов
scripts\test_config.bat     :: демонстрация обработки ошибок
```

Без `run.bat`:

```bash
python src/main.py config.xml
python -m unittest discover -s tests -t . -v
```

## Примеры использования

```
> run.bat config.xml
package=requests
repository=https://pypi.org/pypi
test_mode=false
output_image=C:\...\Pr_2\graph.svg
ascii_tree=true
filter_substring=

> run.bat scripts\errors\bad_test_mode.xml
Ошибка конфигурации: параметр <test_mode> должен быть true или false, получено 'maybe'

> run.bat scripts\errors\bad_output_image.xml
Ошибка конфигурации: файл изображения должен иметь расширение .svg, получено 'graph.png'
```
