"""Получение прямых зависимостей пакета из репозитория PyPI."""

import json
import re
import urllib.error
import urllib.request

TIMEOUT = 15
HTTP_NOT_FOUND = 404
NAME_RE = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
EXTRA_RE = re.compile(r"\bextra\s*==")
SEPARATOR_RE = re.compile(r"[-_.]+")


class RepositoryError(Exception):
    """Ошибка получения данных из репозитория."""


def normalize_name(name):
    """Привести имя пакета к каноническому виду (PEP 503)."""
    return SEPARATOR_RE.sub("-", name).lower()


def package_url(repository, package):
    """Построить URL JSON-описания пакета в репозитории."""
    return f"{repository}/{package}/json"


def fetch_metadata(repository, package):
    """Загрузить JSON-описание последней версии пакета."""
    url = package_url(repository, package)
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == HTTP_NOT_FOUND:
            raise RepositoryError(f"пакет {package!r} не найден") from exc
        raise RepositoryError(f"ошибка HTTP {exc.code}: {url}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RepositoryError(f"не удалось подключиться к {url}") from exc
    try:
        return json.loads(data)
    except ValueError as exc:
        raise RepositoryError(f"некорректный JSON по адресу {url}") from exc


def parse_requirement(line):
    """Извлечь имя пакета из строки Requires-Dist.

    Возвращает None, если зависимость нужна только для extra.
    """
    requirement, _, marker = line.partition(";")
    if EXTRA_RE.search(marker):
        return None
    match = NAME_RE.match(requirement)
    if not match:
        raise RepositoryError(f"не удалось разобрать зависимость {line!r}")
    return normalize_name(match.group(1))


def parse_dependencies(metadata):
    """Получить список прямых зависимостей из JSON-описания пакета."""
    info = metadata.get("info") or {}
    result = []
    for line in info.get("requires_dist") or []:
        name = parse_requirement(line)
        if name and name not in result:
            result.append(name)
    return result


def get_dependencies(repository, package):
    """Вернуть имена прямых зависимостей пакета."""
    return parse_dependencies(fetch_metadata(repository, package))
