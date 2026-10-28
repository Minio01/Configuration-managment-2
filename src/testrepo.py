"""Чтение файла описания тестового репозитория.

Каждая строка файла имеет вид ``A: B C`` — пакет A зависит от B и C.
Пакеты называются большими латинскими буквами. Пустые строки
пропускаются, пакеты без своей строки считаются не имеющими зависимостей.
"""

import re
from pathlib import Path

NAME_RE = re.compile(r"[A-Z]+")


class TestRepositoryError(Exception):
    """Ошибка в файле тестового репозитория."""


def check_name(name, line_number):
    """Проверить имя пакета из строки файла."""
    if not NAME_RE.fullmatch(name):
        raise TestRepositoryError(
            f"строка {line_number}: недопустимое имя пакета {name!r}, "
            "нужны большие латинские буквы"
        )
    return name


def parse_line(line, line_number):
    """Разобрать строку вида 'A: B C' в пару (пакет, зависимости)."""
    package, sep, rest = line.partition(":")
    if not sep:
        raise TestRepositoryError(
            f"строка {line_number}: ожидается формат 'A: B C'"
        )
    package = check_name(package.strip(), line_number)
    deps = [check_name(dep, line_number) for dep in rest.split()]
    return package, deps


def parse_repository(text):
    """Разобрать содержимое тестового репозитория в словарь."""
    repository = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        package, deps = parse_line(line, line_number)
        if package in repository:
            raise TestRepositoryError(
                f"строка {line_number}: пакет {package} описан повторно"
            )
        repository[package] = list(dict.fromkeys(deps))
    return repository


def load_repository(path):
    """Прочитать тестовый репозиторий из файла."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise TestRepositoryError(f"не удалось прочитать {path}") from exc
    return parse_repository(text)
